import streamlit as st
import requests
import uuid

API_URL = "http://backend:8000"

st.set_page_config(
    page_title="AgentCare Portal",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialize Session State for Processing Flag ---
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"session_{uuid.uuid4().hex[:8]}"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Hi, I am an AI HealthCare Agent. How may I assist you today?"
        }
    ]

# --- Sidebar Navigation ---
st.sidebar.title("🏥 AgentCare Portal")
portal_mode = st.sidebar.radio("Select Portal", ["Patient View (Chat)", "Staff View"])

thread_id = st.session_state.thread_id

if portal_mode == "Patient View (Chat)":
    st.title("Patient Assistant & Booking")
    st.markdown("Chat with the AI healthcare assistant to manage appointments, inquiries, and document uploads.")

    # WhatsApp Chat Container Styling
    st.markdown("""
        <style>
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
            margin-bottom: 24px;
        }
        .msg-row {
            display: flex;
            width: 100%;
        }
        .msg-row.user {
            justify-content: flex-end;
        }
        .msg-row.system {
            justify-content: flex-start;
        }
        .bubble {
            max-width: 70%;
            padding: 14px 18px;
            border-radius: 12px;
            font-size: 15px;
            line-height: 1.5;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            word-wrap: break-word;
            margin: 10px;
        }
        .msg-row.user .bubble {
            background-color: #dcf8c6;
            color: #000000;
            border-top-right-radius: 2px;
        }
        .msg-row.system .bubble {
            background-color: #ffffff;
            color: #000000;
            border-top-left-radius: 2px;
            border: 1px solid #e1e4e8;
        }
        .sender-label {
            font-size: 11px;
            color: #666666;
            margin-bottom: 4px;
            font-weight: 600;
        }
        .inline-upload-wrapper {
            position: relative;
            display: flex;
            align-items: center;
        }
        /* Custom styling for the plus button to sit flush inside the input bar */
        div[data-testid="stPopover"] > button {
            border-radius: 50% !important;
            width: 38px !important;
            height: 38px !important;
            padding: 0px !important;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #f0f2f6;
            border: 1px solid #d1d5db;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            margin-top: 24px;
        }
        div[data-testid="stPopover"] > button:hover {
            background-color: #e4e6eb;
            border-color: #b0b7c3;
        }
        </style>
    """, unsafe_allow_html=True)

    # Render chat history
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    last_assistant_index = -1
    for idx, msg in enumerate(st.session_state.messages):
        if msg["role"] == "assistant":
            last_assistant_index = idx

    for idx, message in enumerate(st.session_state.messages):
        role_class = "user" if message["role"] == "user" else "system"
        avatar = "👤 You" if message["role"] == "user" else "🤖 System"
        
        st.markdown(f"""
            <div class="msg-row {role_class}">
                <div class="bubble">
                    <div class="sender-label">{avatar}</div>
                    {message["content"]}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if (
            idx == last_assistant_index 
            and not st.session_state.is_processing 
            and len(st.session_state.messages) > 1
        ):
            st.write("") 
            if st.button("🔄 Start a New Conversation", key=f"new_chat_{idx}"):
                st.session_state.thread_id = f"session_{uuid.uuid4().hex[:8]}"
                st.session_state.messages = [
                    {
                        "role": "assistant", 
                        "content": "Hi, I am an AI HealthCare Agent. How may I assist you today?"
                    }
                ]
                st.rerun()
                
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Integrated Input Area: [+] Upload Button side-by-side with Chat Input ---
    input_col1, input_col2 = st.columns([0.06, 0.94])

    with input_col1:
        # Plus button that opens a popover form for document uploading
        with st.popover("➕", help="Upload a document"):
            st.markdown("### Upload Document")
            with st.form("doc_upload_form"):
                form_patient_id = st.number_input("Patient ID", min_value=1, step=1, format="%d")
                form_doc_type = st.selectbox(
                    "Document Type", 
                    ["Government ID", "Insurance Card", "Medical History", "Intake Form"]
                )
                form_file = st.file_uploader("Select File", type=["pdf", "png", "jpg", "jpeg", "txt"])
                
                submit_doc = st.form_submit_button("Submit Document")
                
                if submit_doc:
                    if form_file is not None and form_patient_id:
                        with st.spinner("Uploading and classifying document..."):
                            try:
                                files = {"file": (form_file.name, form_file.getvalue(), form_file.type)}
                                data = {
                                    "patient_id": str(form_patient_id),
                                    "document_type": form_doc_type
                                }
                                res = requests.post(f"{API_URL}/documents/upload", files=files, data=data)
                                
                                if res.status_code == 200:
                                    res_json = res.json()
                                    st.success(f"Success! Classified as: {res_json.get('document_type')}")
                                    # Append a system chat notification so the history reflects the action
                                    st.session_state.messages.append({
                                        "role": "assistant", 
                                        "content": f"📁 Document uploaded successfully for Patient ID {form_patient_id} (Type: {res_json.get('document_type')}, File: {form_file.name})."
                                    })
                                    st.rerun()
                                else:
                                    st.error(f"Upload failed: {res.text}")
                            except Exception as e:
                                st.error(f"Connection error: {e}")
                    else:
                        st.warning("Please provide Patient ID and select a file.")

    with input_col2:
        if prompt := st.chat_input("Type your message here...", disabled=st.session_state.is_processing):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.is_processing = True
            st.rerun()

    # Process backend response if the last message is from the user and we are in processing mode
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.is_processing:
        latest_prompt = st.session_state.messages[-1]["content"]
        
        with st.spinner("System is thinking..."):
            try:
                payload = {"message": latest_prompt, "thread_id": thread_id}
                response = requests.post(f"{API_URL}/chat", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        data.pop("current_task", None)
                        data.pop("thread_id", None)
                        bot_reply = data.get("response") or data.get("message") or str(data)
                    else:
                        bot_reply = str(data)
                else:
                    bot_reply = f"Error from backend: {response.text}"
            except Exception as e:
                bot_reply = f"Could not connect to backend: {e}"
                
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            st.session_state.is_processing = False
            st.rerun()

elif portal_mode == "Staff View":
    # (Staff view code remains unchanged)
    st.title("Staff & Administration Dashboard")
    st.markdown("View active patient requests, appointments, and handle escalations.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("System Status", "Online", "🟢 Connected")
    col2.metric("Active Thread", thread_id, "Current Session")
    col3.metric("Portal Mode", "Staff Access", "🔐 Authorized")
    
    st.subheader("Actionable Requests & Escalations")
    try:
        res = requests.get(f"{API_URL}/history?thread_id={thread_id}")
        if res.status_code == 200:
            history_data = res.json()
            st.json(history_data)
        else:
            st.info("No pending escalations found in the current session queue.")
    except Exception:
        st.info("Staff review queue is active.")

    st.divider()
    
    action_col1, action_col2 = st.columns(2)
    with action_col1:
        if st.button("Approve Pending Appointment"):
            st.success(f"Appointment for thread `{thread_id}` has been approved.")
    with action_col2:
        if st.button("Escalate to Human Supervisor"):
            st.warning(f"Thread `{thread_id}` has been flagged for human supervisor review.")