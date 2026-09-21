"""OpenAI chat service with lightweight conversation memory."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"

ASSISTANT_MODES = {
    "General Assistant": "You are a helpful, concise general assistant. Ask clarifying questions when useful.",
    "Python Tutor": "You are a patient Python tutor. Explain concepts simply, show small examples, explain code line by line, and end with one practice question.",
    "Coding Assistant": "You are a pragmatic senior coding assistant. Prefer clear, maintainable solutions and mention important edge cases and tests.",
    "Resume Assistant": "You are a professional resume coach. Use measurable, action-oriented language and tailor suggestions to the user's target role.",
    "English Tutor": "You are a supportive English tutor. Correct mistakes gently, explain the correction, and suggest a natural alternative.",
    "Study Assistant": "You are a structured study assistant. Break topics into steps, use active recall, and include a short summary.",
}


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Add it to a .env file before chatting."
        )
    return OpenAI(api_key=api_key)


def _gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Add it to the .env file before chatting."
        )
    return genai.Client(api_key=api_key)


def ask_ai(
    question: str,
    conversation: list[dict[str, str]] | None = None,
    mode: str = "General Assistant",
) -> str:
    """Send a question with prior messages and return the assistant text."""
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("Question cannot be empty.")

    system_prompt = ASSISTANT_MODES.get(mode, ASSISTANT_MODES["General Assistant"])
    provider = os.getenv("AI_PROVIDER", "gemini").strip().lower()

    if provider == "gemini":
        contents: list[types.Content] = []
        for message in conversation or []:
            role = "model" if message["role"] == "assistant" else "user"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=message["content"])],
                )
            )
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=cleaned_question)],
            )
        )
        client = _gemini_client()
        try:
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=system_prompt),
            )
        finally:
            client.close()
        answer = (response.text or "").strip()
    elif provider == "openai":
        messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation or [])
        messages.append({"role": "user", "content": cleaned_question})
        response = _client().responses.create(
            model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
            input=messages,
        )
        answer = response.output_text.strip()
    else:
        raise RuntimeError("AI_PROVIDER must be either 'gemini' or 'openai'.")

    if not answer:
        raise RuntimeError("The AI returned an empty response.")
    return answer
