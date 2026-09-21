import os

from flask import Flask, jsonify, request

from chatbot import ask_ai

app = Flask(__name__)


@app.get("/")
def home():
    return jsonify(
        {
            "status": "ok",
            "message": "AI Chatbot API is running.",
            "provider": os.getenv("AI_PROVIDER", "gemini"),
        }
    )


@app.get("/health")
def health():
    return jsonify({"status": "healthy"})


@app.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip()

    if not question:
        return jsonify({"error": "Question is required."}), 400

    try:
        answer = ask_ai(question)
    except Exception as exc:  # pragma: no cover - defensive error path
        return jsonify({"error": str(exc)}), 500

    return jsonify({"question": question, "answer": answer})


if __name__ == "__main__":
    app.run(debug=True)
