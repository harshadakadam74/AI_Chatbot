"""Streamlit interface for the AI chatbot."""

import streamlit as st

from chatbot import ASSISTANT_MODES, ask_ai
from utils.database import (
    clear_messages,
    create_conversation,
    get_conversation,
    initialize_database,
    list_conversations,
    load_messages,
    save_message,
)

st.set_page_config(page_title="AI Chatbot", page_icon="AI", layout="centered")
initialize_database()

if "conversation_id" not in st.session_state:
    conversations = list_conversations()
    st.session_state.conversation_id = conversations[0]["id"] if conversations else create_conversation("General Assistant")
if "messages" not in st.session_state:
    st.session_state.messages = load_messages(st.session_state.conversation_id)

conversation = get_conversation(st.session_state.conversation_id)
current_mode = str(conversation["mode"]) if conversation else "General Assistant"

with st.sidebar:
    st.header("Assistant")
    selected_mode = st.selectbox("Choose a mode", list(ASSISTANT_MODES), index=list(ASSISTANT_MODES).index(current_mode))
    if selected_mode != current_mode:
        new_id = create_conversation(selected_mode)
        st.session_state.conversation_id = new_id
        st.session_state.messages = []
        st.rerun()

    st.header("Chat history")
    for item in list_conversations():
        label = f"{item['title']} · {item['mode']}"
        if st.button(label, key=f"conversation-{item['id']}", use_container_width=True):
            st.session_state.conversation_id = item["id"]
            st.session_state.messages = load_messages(item["id"])
            st.rerun()

    if st.button("Clear conversation", use_container_width=True):
        clear_messages(st.session_state.conversation_id)
        new_id = create_conversation(current_mode)
        st.session_state.conversation_id = new_id
        st.session_state.messages = []
        st.rerun()

st.title(current_mode)
st.write("Ask questions, explore ideas, and keep the conversation in context.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask something...")

if prompt:
    history = list(st.session_state.messages)
    user_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_message)
    save_message("user", prompt, st.session_state.conversation_id)

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer = ask_ai(prompt, history, current_mode)
            except Exception as error:
                st.error(str(error))
            else:
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                save_message("assistant", answer, st.session_state.conversation_id)
