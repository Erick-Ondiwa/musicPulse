"""RAG assistant orchestration.

This service combines: deterministic SQL analytics, semantic retrieval, optional
LLM answer generation, conversation memory, source reporting, and graceful fallback.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.knowledge import AssistantRun
from app.services.conversations import ConversationService
from app.services.deterministic_assistant import DeterministicAssistantService
from app.services.knowledge import KnowledgeService
from app.services.llm import LLMClient


class AssistantService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.deterministic = DeterministicAssistantService(db)
        self.knowledge = KnowledgeService(db)
        self.conversations = ConversationService(db)
        self.llm = LLMClient()

    def ask(self, question: str, conversation_id: int | None = None) -> dict:
        conversation = self.conversations.get_or_create(conversation_id, question)
        history = self.conversations.history(conversation.id)
        self.conversations.add_message(conversation.id, "user", question)

        # Exact numerical facts continue to come from SQL-backed analytics.
        base = self.deterministic.ask(question)
        sources = self.knowledge.search(question, limit=self.settings.rag_top_k)

        fallback_used = True
        provider = "deterministic-rag"
        model_name = None
        error_message = None
        answer = base["answer"]

        if self.llm.available:
            try:
                answer = self.llm.generate_grounded_answer(
                    question=question,
                    deterministic_answer=base["answer"],
                    metric_definition=base["metric_definition"],
                    structured_data=base["data"],
                    retrieved_sources=sources,
                    conversation_history=history,
                )
                provider = "gemini-generate-content-api"
                model_name = self.settings.gemini_chat_model
                fallback_used = False
            except (httpx.HTTPError, RuntimeError, ValueError, KeyError) as exc:
                # A provider outage must not break the core analytics application.
                error_message = str(exc)

        self.conversations.add_message(conversation.id, "assistant", answer)
        self.db.add(
            AssistantRun(
                conversation_id=conversation.id,
                question=question,
                intent=base["intent"],
                provider=provider,
                model_name=model_name,
                retrieved_source_ids_json=json.dumps([source["document_id"] for source in sources]),
                fallback_used=int(fallback_used),
                error_message=error_message,
            )
        )
        self.db.commit()

        return {
            **base,
            "answer": answer,
            "conversation_id": conversation.id,
            "sources": sources,
            "provider": provider,
            "model_name": model_name,
            "fallback_used": fallback_used,
            "generated_at": datetime.now(timezone.utc),
        }
