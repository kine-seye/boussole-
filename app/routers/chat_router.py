"""
Endpoints du chatbot conversationnel.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.chat_service import poser_question, obtenir_historique

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    user_id: UUID
    message: str


class ChatResponse(BaseModel):
    reponse: str


@router.post("", response_model=ChatResponse)
def envoyer_message(data: ChatRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé. Crée d'abord un profil via /profile.")

    reponse = poser_question(db, data.user_id, data.message)
    return ChatResponse(reponse=reponse)


@router.get("/history/{user_id}")
def get_historique(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé.")

    return {"messages": obtenir_historique(db, user_id)}
