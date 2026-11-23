"""GenAI 聊天机器人 Streamlit 入口。"""

import os

import streamlit as st

import chatbot_lib as glib

st.set_page_config(page_title="Chatbot")
st.title("Chatbot")

username = st.text_input("Enter your username:")
session_id = username
redis_url = os.environ.get("REDIS_URL")
key_prefix = "chat_history:"

if username:
    st.session_state.username = username
    st.info(f"Logged in as: {username}")

if "memory" not in st.session_state:
    st.session_state.memory = glib.get_memory(
        session_id=session_id, url=redis_url, key_prefix=key_prefix
    )

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.session_state.memory = glib.get_memory(
    session_id=session_id, url=redis_url, key_prefix=key_prefix
)

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["text"])

input_text = st.chat_input("Chat with your bot here")

if input_text:
    with st.chat_message("user"):
        st.markdown(input_text)
    st.session_state.chat_history.append({"role": "user", "text": input_text})
    chat_response = glib.get_chat_response(
        input_text=input_text, memory=st.session_state.memory
    )
    with st.chat_message("assistant"):
        st.markdown(chat_response)
    st.session_state.chat_history.append({"role": "assistant", "text": chat_response})