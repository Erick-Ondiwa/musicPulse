"""HTTP endpoints for grounded AI conversations and history."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.knowledge import Conversation
from app.schemas import AskRequest, AskResponse
from app.services.assistant import AssistantService
from app.services.conversations import ConversationService

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, db: Session = Depends(get_db)):
    return AssistantService(db).ask(payload.question, payload.conversation_id)


@router.get("/conversations")
def list_conversations(
    limit: int = Query(default=30, ge=1, le=100), db: Session = Depends(get_db)
):
    conversations = ConversationService(db).list_conversations(limit)
    return [
        {"id": item.id, "title": item.title, "created_at": item.created_at, "updated_at": item.updated_at}
        for item in conversations
    ]


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "id": conversation.id,
        "title": conversation.title,
        "messages": [
            {"id": message.id, "role": message.role, "content": message.content, "created_at": message.created_at}
            for message in conversation.messages
        ],
    }
