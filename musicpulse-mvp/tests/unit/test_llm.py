"""Gemini client tests validate request shape and response parsing without network."""

from app.core.config import Settings
from app.services.llm import LLMClient


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "candidates": [
                {"content": {"parts": [{"text": "Grounded Gemini answer"}]}}
            ]
        }


def test_gemini_generate_content_request(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr("app.services.llm.httpx.post", fake_post)
    client = LLMClient(
        Settings(
            gemini_api_key="test-key",
            gemini_chat_model="gemini-2.5-flash",
        )
    )
    answer = client.generate_grounded_answer(
        question="What is trending?",
        deterministic_answer="Song A is first.",
        metric_definition="View growth over time.",
        structured_data=[],
        retrieved_sources=[],
        conversation_history=[],
    )

    assert answer == "Grounded Gemini answer"
    assert captured["url"].endswith("/models/gemini-2.5-flash:generateContent")
    assert captured["headers"]["x-goog-api-key"] == "test-key"
    assert "systemInstruction" in captured["json"]
    assert captured["json"]["contents"][0]["role"] == "user"
