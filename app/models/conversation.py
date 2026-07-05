"""
Suit la progression de chaque conversation WhatsApp : à quelle question on en est,
et les réponses déjà collectées avant de les valider en base dans UserProfile.

Nécessaire car WhatsApp est un canal asynchrone message-par-message : contrairement
au dashboard où tout le formulaire est rempli avant soumission, ici on doit se souvenir
d'où l'utilisateur en est entre deux messages.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ConversationState(Base):
    __tablename__ = "conversation_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    whatsapp_number = Column(String(20), unique=True, nullable=False, index=True)

    etape_courante = Column(String(50), default="debut")
    # ex: "debut", "attente_age", "attente_diplome", "attente_domaine",
    # "attente_experience", "attente_langue_fr", "attente_langue_en",
    # "attente_capacite_financiere", "attente_pays", "attente_demarche", "termine"

    reponses_temporaires = Column(JSON, default=dict)
    # stocke les réponses au fur et à mesure, avant de les valider dans UserProfile
    # une fois toutes les questions répondues

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
