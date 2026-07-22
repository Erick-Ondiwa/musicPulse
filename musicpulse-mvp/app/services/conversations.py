"""Persistence helpers for multi-turn assistant conversations."""

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.knowledge import ChatMessage, Conversation


class ConversationService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, conversation_id: int | None, first_question: str) -> Conversation:
        conversation = self.db.get(Conversation, conversation_id) if conversation_id else None
        if conversation is None:
            title = first_question.strip()[:80] or "New music intelligence chat"
            conversation = Conversation(title=title)
            self.db.add(conversation)
            self.db.flush()
        return conversation

    def add_message(self, conversation_id: int, role: str, content: str) -> ChatMessage:
        message = ChatMessage(conversation_id=conversation_id, role=role, content=content)
        self.db.add(message)
        self.db.flush()
        return message

    def history(self, conversation_id: int, limit: int = 12) -> list[dict]:
        messages = self.db.scalars(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
        ).all()
        return [
            {"role": message.role, "content": message.content}
            for message in reversed(messages)
        ]

    def list_conversations(self, limit: int = 30) -> list[Conversation]:
        return self.db.scalars(
            select(Conversation).order_by(desc(Conversation.updated_at)).limit(limit)
        ).all()
