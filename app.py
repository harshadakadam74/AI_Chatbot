
"""Streamlit interface for the AI chatbot."""

import os

from flask import Flask
import streamlit as st
from dotenv import load_dotenv

from auth import login, register
from chatbot import ASSISTANT_MODES, ask_ai
from utils.database import (
    clear_messages,
    create_conversation,
    get_conversation,
    initialize_database,
    list_conversations,
    load_messages,
    save_message,
    update_conversation_title,
)

st.set_page_config(page_title="AI Chatbot", page_icon="AI", layout="centered")
initialize_database()
load_dotenv()

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
        --ink: #e8eaf3;
        --muted: #9298ad;
        --panel: #171a28;
        --panel-soft: #1d2132;
        --line: rgba(146, 152, 173, 0.16);
        --accent: #8c7cff;
        --accent-bright: #b4a9ff;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background: #0d0f18;
        color: var(--ink);
        font-family: 'DM Sans', sans-serif;
    }

    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background: #11131f;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }
    [data-testid="stMainBlockContainer"] { max-width: 860px; padding-top: 2.75rem; }

    h1, h2, h3, [data-testid="stSidebar"] h2 {
        font-family: 'Space Grotesk', sans-serif;
        letter-spacing: 0;
    }
    h1 { font-size: 2.35rem; margin-bottom: 0.25rem; }
    [data-testid="stSidebar"] h2 { font-size: 1rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); }
    [data-testid="stMarkdownContainer"] p { color: var(--muted); }

    .brand {
        padding: 0 0.25rem 1.8rem;
        border-bottom: 1px solid var(--line);
        margin-bottom: 1.8rem;
    }
    .brand-mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2.1rem;
        height: 2.1rem;
        margin-right: 0.55rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #8c7cff, #4d9fff);
        color: white;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
    }
    .brand-name { color: var(--ink); font: 700 1.05rem 'Space Grotesk', sans-serif; vertical-align: 0.25rem; }
    .brand-copy { color: var(--muted); font-size: 0.8rem; margin: 0.65rem 0 0; }

    .mode-card {
        background: linear-gradient(135deg, rgba(140, 124, 255, 0.18), rgba(77, 159, 255, 0.08));
        border: 1px solid rgba(140, 124, 255, 0.3);
        border-radius: 12px;
        padding: 1rem 1.1rem;
        margin: 1.3rem 0 2rem;
    }
    .mode-label { color: var(--muted); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.12em; }
    .mode-name { color: var(--accent-bright); font: 600 1rem 'Space Grotesk', sans-serif; margin-top: 0.3rem; }

    .empty-state {
        border: 1px dashed rgba(140, 124, 255, 0.38);
        border-radius: 16px;
        background: radial-gradient(circle at 50% 0%, rgba(140, 124, 255, 0.12), transparent 58%), var(--panel);
        padding: 4rem 2rem;
        text-align: center;
        margin: 2rem 0 1rem;
    }
    .empty-icon { font-size: 2rem; color: var(--accent-bright); }
    .empty-title { color: var(--ink); font: 600 1.25rem 'Space Grotesk', sans-serif; margin: 0.75rem 0 0.35rem; }
    .empty-copy { color: var(--muted); margin: 0; }

    [data-testid="stChatMessage"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        background: var(--panel);
        padding: 1rem 1.15rem;
        margin: 0.75rem 0;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p { color: var(--ink); }
    [data-testid="stChatInput"] { border-color: rgba(140, 124, 255, 0.4); }
    [data-testid="stChatInput"] textarea { color: var(--ink); }

    .stButton > button, .stSelectbox [data-baseweb="select"] > div {
        background: var(--panel-soft);
        border: 1px solid var(--line);
        color: var(--ink);
        border-radius: 9px;
    }
    .stButton > button:hover { border-color: var(--accent); color: white; }
    [data-testid="stSidebar"] .stButton > button { text-align: left; font-size: 0.82rem; }
    [data-testid="stSidebar"] .stButton:last-child > button { color: #ff9caa; margin-top: 1rem; }
    [data-testid="stSidebar"] [data-testid="stExpander"] { border-color: var(--line); background: transparent; }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary { color: var(--muted); }
    [data-testid="stPills"] button { border-color: var(--line); background: var(--panel-soft); color: var(--ink); }
    [data-testid="stPills"] button:hover { border-color: var(--accent); }
    .chat-meta { color: var(--muted); font-size: 0.82rem; margin-top: -0.2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.session_state.setdefault("logged_in", False)

if not st.session_state.logged_in:
    st.markdown('<div class="empty-state auth-card">', unsafe_allow_html=True)
    st.markdown('<div class="empty-icon">AI</div><div class="empty-title">Gemini AI Hub</div>', unsafe_allow_html=True)
    st.caption("Your private workspace for helpful conversations.")
    login_tab, register_tab = st.tabs(["Login", "Create account"])

    with login_tab:
        with st.form("login-form"):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", width="stretch")
        if submitted:
            user = login(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_id = int(user["id"])
                st.session_state.user_name = str(user["name"])
                st.session_state.user_email = str(user["email"])
                st.rerun()
            st.error("Invalid email or password.")

    with register_tab:
        with st.form("register-form"):
            name = st.text_input("Name", placeholder="Your name")
            email = st.text_input("Email", placeholder="you@example.com", key="register-email")
            password = st.text_input("Password", type="password", key="register-password")
            confirmation = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Register", width="stretch")
        if submitted:
            success, message = register(name, email, password, confirmation)
            (st.success if success else st.error)(message)

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

user_id = int(st.session_state["user_id"])

if "conversation_id" not in st.session_state:
    conversations = list_conversations(user_id)
    st.session_state.conversation_id = conversations[0]["id"] if conversations else create_conversation(user_id, "General Assistant")
if "messages" not in st.session_state:
    st.session_state.messages = load_messages(st.session_state.conversation_id, user_id)

conversation = get_conversation(st.session_state.conversation_id, user_id)
if conversation is None:
    st.session_state.conversation_id = create_conversation(user_id, "General Assistant")
    st.session_state.messages = []
    conversation = get_conversation(st.session_state.conversation_id, user_id)
current_mode = str(conversation["mode"]) if conversation else "General Assistant"

with st.sidebar:
    st.markdown(
        '<div class="brand"><span class="brand-mark">AI</span><span class="brand-name">AI CHATBOT</span>'
        '<p class="brand-copy">A focused space for better conversations.</p></div>',
        unsafe_allow_html=True,
    )
    if st.button(":material/edit_square:  New chat", width="stretch"):
        new_id = create_conversation(user_id, current_mode)
        st.session_state.conversation_id = new_id
        st.session_state.messages = []
        st.rerun()

    st.markdown('<div class="mode-label">Assistant mode</div>', unsafe_allow_html=True)
    selected_mode = st.selectbox(
        "Choose a mode",
        list(ASSISTANT_MODES),
        index=list(ASSISTANT_MODES).index(current_mode),
        label_visibility="collapsed",
    )
    if selected_mode != current_mode:
        new_id = create_conversation(user_id, selected_mode)
        st.session_state.conversation_id = new_id
        st.session_state.messages = []
        st.rerun()

    st.markdown('<div class="mode-card"><div class="mode-label">Active mode</div><div class="mode-name">'
                f'{current_mode}</div></div>', unsafe_allow_html=True)
    st.header(":material/history: Chat history")
    for item in list_conversations(user_id):
        label = f"{item['title']} · {item['mode']}"
        if st.button(label, key=f"conversation-{item['id']}", width="stretch"):
            st.session_state.conversation_id = item["id"]
            st.session_state.messages = load_messages(item["id"], user_id)
            st.rerun()

    if st.button(":material/delete_sweep:  Clear conversation", width="stretch"):
        clear_messages(st.session_state.conversation_id, user_id)
        new_id = create_conversation(user_id, current_mode)
        st.session_state.conversation_id = new_id
        st.session_state.messages = []
        st.rerun()

    with st.expander(":material/tune:  Settings"):
        provider = os.getenv("AI_PROVIDER", "gemini").strip().lower()
        st.caption(f"Provider: {provider.title()}")
        st.caption("Conversations are stored locally in SQLite.")
        st.caption(f"Signed in as {st.session_state['user_email']}")
        if st.button(":material/logout:  Log out", width="stretch"):
            st.session_state.clear()
            st.rerun()

st.title(current_mode)
st.markdown('<div class="chat-meta">Your intelligent assistant for focused conversations.</div>', unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown(
        '<div class="empty-state"><div class="empty-icon">AI</div>'
        '<div class="empty-title">Ready when you are</div>'
        '<p class="empty-copy">Start a conversation below and let us work through it together.</p></div>',
        unsafe_allow_html=True,
    )
    suggestions = {
        ":material/lightbulb: Explain a concept": "Explain a concept simply with an example",
        ":material/code: Help me write code": "Help me write a clean Python function",
        ":material/summarize: Summarize something": "Summarize the key points of a topic",
    }
    selected_suggestion = st.pills(
        "Try a prompt",
        list(suggestions),
        label_visibility="collapsed",
    )
else:
    selected_suggestion = None

if st.session_state.messages:
    export_text = "\n\n".join(
        f"{message['role'].title()}\n{message['content']}"
        for message in st.session_state.messages
    )
    st.download_button(
        ":material/download: Export chat",
        export_text,
        file_name="ai-chat.txt",
        mime="text/plain",
        width="content",
    )

for message in st.session_state.messages:
    avatar = ":material/person:" if message["role"] == "user" else ":material/smart_toy:"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

prompt = st.chat_input("Ask anything...")
if selected_suggestion:
    prompt = suggestions[selected_suggestion]

if prompt:
    history = list(st.session_state.messages)
    user_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_message)
    save_message("user", prompt, st.session_state.conversation_id, user_id)
    if not history:
        update_conversation_title(st.session_state.conversation_id, user_id, prompt)

    with st.chat_message("user", avatar=":material/person:"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=":material/smart_toy:"):
        with st.spinner("Thinking..."):
            try:
                answer = ask_ai(prompt, history, current_mode)
            except Exception as error:
                st.error(str(error))
            else:
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                save_message("assistant", answer, st.session_state.conversation_id, user_id)
