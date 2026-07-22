"""Gemini API client for evidence-grounded answer generation.

The model never receives direct database access. It receives only the trusted
analytics and retrieval evidence assembled by the backend RAG services.
"""

from __future__ import annotations

import json
import httpx

from app.core.config import Settings, get_settings


SYSTEM_INSTRUCTIONS = """You are MusicPulse AI, a careful music intelligence analyst.
Use only the supplied structured analytics and retrieved evidence. Never invent metrics.
State limitations clearly: YouTube views are not equivalent to global streams, and the
MusicPulse trend score is application-defined. Give a concise, useful answer, explain
important comparisons, and mention supporting source titles when relevant."""


class LLMClient:
    """Call Gemini's generateContent REST endpoint with grounded RAG evidence."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    @property
    def available(self) -> bool:
        """Expose whether Gemini is enabled and a key has been configured."""
        return self.settings.llm_available

    def generate_grounded_answer(
        self,
        *,
        question: str,
        deterministic_answer: str,
        metric_definition: str,
        structured_data: list[dict],
        retrieved_sources: list[dict],
        conversation_history: list[dict],
    ) -> str:
        """Generate an answer using only evidence supplied by MusicPulse services."""
        if not self.available:
            raise RuntimeError("Gemini is not configured")

        evidence = {
            "question": question,
            "deterministic_analysis": deterministic_answer,
            "metric_definition": metric_definition,
            "structured_data": structured_data[:10],
            "retrieved_sources": [
                {
                    "title": source["title"],
                    "content": source["content"][:1200],
                    "score": source["score"],
                    "source_url": source.get("source_url"),
                }
                for source in retrieved_sources
            ],
            "recent_conversation": conversation_history[-6:],
        }

        model = self.settings.gemini_chat_model.strip()
        endpoint = (
            f"{self.settings.gemini_base_url.rstrip('/')}/models/"
            f"{model}:generateContent"
        )
        prompt = (
            "Answer the user's music-intelligence question using this JSON evidence. "
            "Do not claim access to information outside it.\n\n"
            + json.dumps(evidence, default=str)
        )

        response = httpx.post(
            endpoint,
            headers={
                "x-goog-api-key": self.settings.gemini_api_key,
                "Content-Type": "application/json",
            },
            json={
                "systemInstruction": {
                    "parts": [{"text": SYSTEM_INSTRUCTIONS}],
                },
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 1200,
                },
            },
            timeout=self.settings.llm_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()

        # Gemini returns text inside candidates[].content.parts[].text.
        candidates = payload.get("candidates") or []
        if not candidates:
            feedback = payload.get("promptFeedback") or {}
            reason = feedback.get("blockReason", "no candidate returned")
            raise ValueError(f"Gemini response contained no answer: {reason}")

        fragments = [
            part["text"]
            for part in candidates[0].get("content", {}).get("parts", [])
            if part.get("text")
        ]
        if not fragments:
            raise ValueError("Gemini response did not contain output text")
        return "\n".join(fragments).strip()
