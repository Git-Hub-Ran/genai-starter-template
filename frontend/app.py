"""Streamlit frontend (the UI). It only talks to the backend, never to the LLM directly,
so the API key never reaches the browser.

Run locally:  streamlit run app.py
"""
import os

import requests
import streamlit as st

#the backend's address: 
#It reads the BACKEND_URL setting, and if there isn't one, it uses localhost:8000.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
TIMEOUT_SECONDS = 60 #don't wait more than 60 seconds for the backend

#set the page's tab title, icon, and heading.
st.set_page_config(page_title="GenAI Interview Starter", page_icon="💬")
st.title("GenAI Interview Starter")
st.caption("Replace this title and caption with your idea.")

#sends the message to /api/chat:
def ask_backend(message: str) -> str:
    try:
        resp = requests.post(f"{BACKEND_URL}/api/chat", json={"message": message}, timeout=TIMEOUT_SECONDS)
    except requests.RequestException:
        return "⚠️ Can't reach the backend. Check that it is running and that BACKEND_URL is correct."

    if resp.ok:
        return resp.json()["answer"]

    try:
        detail = resp.json().get("detail", "Unknown error")
    except ValueError:
        detail = f"Backend error ({resp.status_code})."
    if isinstance(detail, list):  # FastAPI validation errors come as a list
        detail = "Your message is empty or too long."
    return f"⚠️ {detail}"

#session_state is the memory that survives, and here it keeps the chat history( because the page is redrawn every time the user types a message).
if "messages" not in st.session_state:
    st.session_state.messages = []

#this loop show all the previous messages again, because the page is redrawn every time.
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

#shows the text box:
if prompt := st.chat_input("Type a message"): #The := saves what the user typed and checks that it's not empty, in one line.
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = ask_backend(prompt)
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
