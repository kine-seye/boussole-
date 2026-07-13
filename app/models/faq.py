"""
FAQ curée manuellement : réponses à des questions fréquentes qui ne rentrent pas dans
le modèle "critère d'éligibilité" (ex: frais de visa, délais de traitement généraux).
Chaque entrée DOIT avoir une source officielle citée — jamais de chiffre sans preuve.
"""
import uuid

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class FAQEntry(Base):
    __tablename__ = "faq_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pays = Column(String(100), nullable=False, index=True)
    type_demarche = Column(String(100), nullable=True)  # NULL = s'applique à toutes les démarches du pays
    sujet = Column(String(255), nullable=False)  # ex: "frais_visa", "delai_traitement"
    question_type = Column(String(255), nullable=False)  # ex: "Combien coûte le visa étudiant ?"
    reponse = Column(Text, nullable=False)
    source_officielle = Column(String(500), nullable=False)
    date_verification = Column(String(20), nullable=False)  # ex: "2026-07" pour savoir si périmé
