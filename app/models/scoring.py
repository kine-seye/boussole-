"""
Historique des résultats de scoring.
Utile dès la Phase 1 pour que l'utilisateur revoie son dernier résultat sans tout recalculer,
et sert de fondation pour le suivi de candidatures en Phase 2.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ScoringResult(Base):
    __tablename__ = "scoring_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    pays = Column(String(100), nullable=False)
    type_demarche = Column(String(100), nullable=False)

    score_total = Column(Float, nullable=False)  # 0-100
    tranche = Column(String(50), nullable=False)  # "Élevé", "Moyen", "Faible" - pas de fausse précision
    eliminatoire_manquant = Column(JSON, default=list)  # liste des critères éliminatoires non remplis

    details_criteres = Column(JSON, nullable=False)  # snapshot complet ✅❌ par critère
    plan_coaching = Column(JSON, nullable=True)  # snapshot du plan d'action généré

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="scoring_history")
