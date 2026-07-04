"""
Modèles utilisateur et profil.

Un User peut avoir un seul UserProfile qui est enrichi progressivement :
- d'abord via le questionnaire déclaratif
- puis via l'extraction CV, qui vient COMPLÉTER (jamais écraser silencieusement)
  les champs déjà déclarés
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, Enum, JSON, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class LanguageLevel(str, enum.Enum):
    AUCUN = "aucun"
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    whatsapp_number = Column(String(20), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("UserProfile", back_populates="user", uselist=False)
    scoring_history = relationship("ScoringResult", back_populates="user")


class UserProfile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    # Identité / démographie
    age = Column(Integer, nullable=True)
    nationalite = Column(String(100), default="Sénégal")

    # Éducation
    niveau_diplome = Column(String(100), nullable=True)  # Bac, Bac+2, Licence, Master, Doctorat
    domaine_etude = Column(String(255), nullable=True)
    etablissement = Column(String(255), nullable=True)
    annee_obtention = Column(Integer, nullable=True)

    # Expérience professionnelle
    annees_experience = Column(Float, default=0)
    secteur_activite = Column(String(255), nullable=True)
    poste_actuel = Column(String(255), nullable=True)

    # Langues (stockées en JSON : {"français": "C2", "anglais": "B1"})
    langues = Column(JSON, default=dict)

    # Situation financière déclarée (en FCFA, tranche large pour rester simple)
    capacite_financiere_fcfa = Column(Integer, nullable=True)

    # Pays et démarche ciblés (l'utilisateur peut en avoir plusieurs -> table à part si besoin plus tard)
    pays_cible = Column(String(100), nullable=True)
    type_demarche = Column(String(100), nullable=True)  # "visa_etudiant", "bourse", "visa_travail"

    # Traçabilité de la source des données
    donnees_source = Column(String(50), default="questionnaire")  # "questionnaire", "cv", "mixte"
    cv_brut_json = Column(JSON, nullable=True)  # sauvegarde de l'extraction CV brute

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
