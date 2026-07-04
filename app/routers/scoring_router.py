"""
Endpoint principal : calcule le score, génère le coaching, retourne le tout.
C'est ici que scoring_service + coach_service se combinent.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UserProfile
from app.models.scoring import ScoringResult
from app.schemas.profile_schema import ScoringRequest, ScoringResponse
from app.services.scoring_service import calculer_score
from app.services.coach_service import generer_plan_coaching

router = APIRouter(prefix="/score", tags=["scoring"])


@router.post("", response_model=ScoringResponse)
def evaluer_chances(data: ScoringRequest, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == data.user_id).first()
    if not profile:
        raise HTTPException(404, "Profil non trouvé. Complète d'abord ton profil via /profile.")

    try:
        resultat_scoring = calculer_score(db, profile, data.pays, data.type_demarche)
    except ValueError as e:
        raise HTTPException(404, str(e))

    plan_coaching = generer_plan_coaching(resultat_scoring)

    # Sauvegarde en historique (fondation pour le suivi de candidatures en Phase 2)
    historique = ScoringResult(
        user_id=data.user_id,
        pays=resultat_scoring.pays,
        type_demarche=resultat_scoring.type_demarche,
        score_total=resultat_scoring.score_brut,
        tranche=resultat_scoring.tranche,
        eliminatoire_manquant=resultat_scoring.criteres_manquants_eliminatoires,
        details_criteres=[
            {
                "libelle": c.libelle, "rempli": c.rempli, "eliminatoire": c.eliminatoire,
                "valeur_requise": c.valeur_requise, "valeur_utilisateur": c.valeur_utilisateur,
            }
            for c in resultat_scoring.criteres
        ],
        plan_coaching=plan_coaching,
    )
    db.add(historique)
    db.commit()

    return ScoringResponse(
        pays=resultat_scoring.pays,
        type_demarche=resultat_scoring.type_demarche,
        tranche=resultat_scoring.tranche,
        eligible=resultat_scoring.eligible,
        criteres=[
            {
                "libelle": c.libelle, "type_critere": c.type_critere,
                "valeur_requise": c.valeur_requise, "valeur_utilisateur": c.valeur_utilisateur,
                "rempli": c.rempli, "eliminatoire": c.eliminatoire, "explication": c.explication,
            }
            for c in resultat_scoring.criteres
        ],
        criteres_manquants_eliminatoires=resultat_scoring.criteres_manquants_eliminatoires,
        plan_coaching=plan_coaching,
    )
