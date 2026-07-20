import streamlit as st
import logging
import http.client as http_client
import requests

# This will print full HTTP request/response headers to the Docker terminal
http_client.HTTPConnection.debuglevel = 1
logging.basicConfig(level=logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

st.title("Agentic Healthcare Assistant")
st.write("End-to-End Connection Test")

# 1. Initialize session state to hold chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. Display previous chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 3. Create the chat input box
if prompt := st.chat_input("Type a message to test the routing..."):
    
    # Display the user's message on the screen immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 4. Send the message to the FastAPI backend
    try:
        # Note: We use "http://backend:8000" because of Docker's internal network!
        payload = {"message": prompt, "user_id": "test_user_01"}
        response = requests.post(
            "http://backend:8000/chat", 
            json=payload
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Extract the AI's response from the JSON payload
        data = response.json()
        ai_reply = data.get("response")
        task_status = data.get("task_status")
        
        # Display the AI's response with some debug info
        with st.chat_message("assistant"):
            st.markdown(f"**AI:** {ai_reply}")
            st.caption(f"Debug Info - Status: {task_status}")
            
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})

    except requests.exceptions.ConnectionError:
        st.error("🚨 Could not connect to the backend. Is the backend container running?")
    except Exception as e:
        st.error(f"🚨 An error occurred: {e}")