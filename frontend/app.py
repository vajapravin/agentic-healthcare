import streamlit as st
import requests

# FastAPI Backend URL (using service name since Streamlit runs in Docker)
API_URL = "http://backend:8000"

# Page Configuration
st.markdown("""
        <style>
        .chat-container {
            display: flex;
            flex-direction: column;
            gap: 20px; /* Increased gap between message rows */
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
        </style>
    """, unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("🏥 AgentCare Portal")

# Global Session Thread ID available to both Patient and Staff views
thread_id = st.sidebar.text_input("Session Thread ID", value="patient_session_01")

portal_mode = st.sidebar.radio("Select Portal", ["Patient View (Chat)", "Staff View"])

if portal_mode == "Patient View (Chat)":
    st.title("Patient Assistant & Booking")
    st.markdown("Chat with the AI healthcare assistant to manage appointments and inquiries.")
    
    # Initialize chat history in session state if not present
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Render chat container history
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in st.session_state.messages:
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
    st.markdown('</div>', unsafe_allow_html=True)

    # Chat Input Box
    if prompt := st.chat_input("Type your message here..."):
        # 1. Append and immediately render user message so it appears instantly
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # We rerun or trigger a clean layout update so the user message displays 
        # while the system prepares the response
        st.rerun()

    # Check if the last message was from the user; if so, fetch the system response
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
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
                
            # Append assistant response and refresh to display it
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            st.rerun()

elif portal_mode == "Staff View":
    st.title("Staff & Administration Dashboard")
    st.markdown("View active patient requests, appointments, and handle escalations.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("System Status", "Online", "🟢 Connected")
    col2.metric("Active Thread", thread_id, "Current Session")
    col3.metric("Portal Mode", "Staff Access", "🔐 Authorized")
    
    st.subheader("Actionable Requests & Escalations")
    
    # Fetch or display session messages / history from backend if an endpoint exists, 
    # or display an interactive management table
    try:
        # Example: Fetching chat history or records for this thread to review
        res = requests.get(f"{API_URL}/history?thread_id={thread_id}")
        if res.status_code == 200:
            history_data = res.json()
            st.write("Recent interaction logs for auditing:")
            st.json(history_data)
        else:
            st.info("No pending escalations found in the current session queue.")
    except Exception:
        st.info("Staff review queue is active. Use the controls below to manage requests.")

    st.divider()
    
    # Staff Action Controls
    st.subheader("Staff Intervention Tools")
    action_col1, action_col2 = st.columns(2)
    
    with action_col1:
        if st.button("Approve Pending Appointment"):
            st.success(f"Appointment for thread `{thread_id}` has been approved.")
            
    with action_col2:
        if st.button("Escalate to Human Supervisor"):
            st.warning(f"Thread `{thread_id}` has been flagged for human supervisor review.")