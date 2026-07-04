"""
Modèles pour les critères d'éligibilité par pays/démarche, et les checklists documentaires.

C'est le coeur "métier" curé manuellement pour la Phase 1 (pas de scraping temps réel).
"""
import uuid
import enum

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class TypeCritere(str, enum.Enum):
    NIVEAU_DIPLOME = "niveau_diplome"
    LANGUE = "langue"
    EXPERIENCE = "experience"
    AGE = "age"
    CAPACITE_FINANCIERE = "capacite_financiere"
    DOMAINE_ETUDE = "domaine_etude"
    AUTRE = "autre"


class CountryCriteria(Base):
    """
    Une ligne = un critère d'éligibilité pour un couple (pays, type_demarche).
    Ex: (Canada, visa_etudiant, LANGUE, "IELTS 6.0", poids=20, eliminatoire=True)
    """
    __tablename__ = "countries_criteria"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pays = Column(String(100), nullable=False, index=True)
    type_demarche = Column(String(100), nullable=False, index=True)  # visa_etudiant, bourse, visa_travail

    type_critere = Column(Enum(TypeCritere), nullable=False)
    libelle = Column(String(255), nullable=False)  # texte lisible: "Niveau d'anglais IELTS"
    valeur_requise = Column(String(255), nullable=False)  # "6.0", "Bac+2", "25 ans max"
    valeur_requise_numerique = Column(Float, nullable=True)  # pour comparaison automatique quand possible

    poids = Column(Integer, default=10)  # contribution au score sur 100
    eliminatoire = Column(Boolean, default=False)  # si non rempli -> score plafonné/rejeté

    explication = Column(Text, nullable=True)  # pourquoi ce critère compte, aide au coaching
    source_officielle = Column(String(500), nullable=True)  # URL de référence officielle


class DocumentChecklist(Base):
    """
    Une ligne = un document requis pour un couple (pays, type_demarche).
    Indépendant du scoring : c'est purement informatif/procédural.
    """
    __tablename__ = "documents_checklist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pays = Column(String(100), nullable=False, index=True)
    type_demarche = Column(String(100), nullable=False, index=True)

    document = Column(String(255), nullable=False)  # "Passeport valide 6 mois"
    delai_obtention_estime = Column(String(100), nullable=True)  # "2-4 semaines"
    obligatoire = Column(Boolean, default=True)
    ordre_affichage = Column(Integer, default=0)  # pour respecter un ordre logique (passeport avant visa...)
    remarque = Column(Text, nullable=True)
