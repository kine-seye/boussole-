"""
Historique des messages du chatbot conversationnel (questions libres, distinct de
ConversationState qui gère le flux structuré WhatsApp étape par étape).
Persisté par utilisateur pour que l'historique survive entre les sessions/canaux
(dashboard et WhatsApp partagent le même historique si le même user_id est utilisé).
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" ou "assistant"
    contenu = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
