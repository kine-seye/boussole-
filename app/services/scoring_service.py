"""
Moteur de scoring : compare un UserProfile aux CountryCriteria d'un (pays, type_demarche)
et produit un résultat détaillé critère par critère.

Principe volontairement conservateur :
- Un score numérique existe en interne (pour prioriser le coaching)
- Mais on n'affiche JAMAIS ce chiffre brut à l'utilisateur avec une fausse précision.
  On affiche une TRANCHE ("Élevé", "Moyen", "Faible") + le détail ✅❌.
  Voir DECISIONS.md pour la justification (éviter la fausse certitude sur des sujets
  à fort enjeu comme l'immigration).
"""
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from app.models.criteria import CountryCriteria, TypeCritere
from app.models.user import UserProfile


@dataclass
class CritereResultat:
    libelle: str
    type_critere: str
    valeur_requise: str
    valeur_utilisateur: Optional[str]
    rempli: bool
    eliminatoire: bool
    poids: int
    explication: Optional[str] = None


@dataclass
class ScoringResultat:
    pays: str
    type_demarche: str
    score_brut: float  # 0-100, usage interne (priorisation coaching)
    tranche: str  # "Élevé" / "Moyen" / "Faible" - c'est CE QUI est affiché à l'utilisateur
    eligible: bool  # False si un critère éliminatoire manque
    criteres: list[CritereResultat] = field(default_factory=list)
    criteres_manquants_eliminatoires: list[str] = field(default_factory=list)


def _score_vers_tranche(score: float, eligible: bool) -> str:
    """
    Convertit un score numérique en tranche qualitative.
    Un critère éliminatoire manquant plafonne automatiquement en 'Faible',
    même si le score numérique brut serait élevé par ailleurs.
    """
    if not eligible:
        return "Faible"
    if score >= 75:
        return "Élevé"
    if score >= 50:
        return "Moyen"
    return "Faible"


def _extraire_valeur_utilisateur(profile: UserProfile, type_critere: TypeCritere) -> Optional[str]:
    """Récupère la valeur pertinente du profil selon le type de critère évalué."""
    mapping = {
        TypeCritere.NIVEAU_DIPLOME: profile.niveau_diplome,
        TypeCritere.EXPERIENCE: f"{profile.annees_experience} an(s)" if profile.annees_experience is not None else None,
        TypeCritere.AGE: str(profile.age) if profile.age is not None else None,
        TypeCritere.CAPACITE_FINANCIERE: str(profile.capacite_financiere_fcfa) if profile.capacite_financiere_fcfa else None,
        TypeCritere.DOMAINE_ETUDE: profile.domaine_etude,
    }
    if type_critere == TypeCritere.LANGUE:
        if not profile.langues:
            return None
        # on retourne la meilleure langue déclarée pour affichage simple
        return ", ".join(f"{k}: {v}" for k, v in profile.langues.items())
    return mapping.get(type_critere)


# Ordres de niveau pour comparaisons simples (diplôme)
NIVEAUX_DIPLOME_ORDRE = {
    "Bac": 1, "Bac+2": 2, "Licence": 2, "Bac+3": 2,
    "Master": 3, "Bac+5": 3, "Doctorat": 4, "PhD": 4,
}

NIVEAUX_LANGUE_ORDRE = {"AUCUN": 0, "A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}


def _evaluer_critere(critere: CountryCriteria, profile: UserProfile) -> bool:
    """
    Détermine si un critère est rempli. Logique simple et explicite (pas de magie),
    volontairement lisible pour que le coaching puisse expliquer le "pourquoi".
    """
    tc = critere.type_critere

    if tc == TypeCritere.NIVEAU_DIPLOME:
        niveau_user = NIVEAUX_DIPLOME_ORDRE.get(profile.niveau_diplome or "", 0)
        niveau_requis = critere.valeur_requise_numerique or 0
        return niveau_user >= niveau_requis

    if tc == TypeCritere.AGE:
        if profile.age is None:
            return False
        # ici valeur_requise_numerique est un PLAFOND (ex: "25 ans max")
        return profile.age <= (critere.valeur_requise_numerique or 999)

    if tc == TypeCritere.CAPACITE_FINANCIERE:
        if not profile.capacite_financiere_fcfa:
            return False
        # conversion approximative FCFA -> devise cible non faite ici (Phase 2),
        # on compare de façon conservatrice : on considère le critère "à vérifier" si non converti
        # Pour le MVP on suppose que le seuil a déjà été converti en FCFA au moment du seed
        # -> simplification assumée et documentée
        return profile.capacite_financiere_fcfa >= (critere.valeur_requise_numerique or 0)

    if tc == TypeCritere.LANGUE:
        if not profile.langues:
            return False
        meilleur_niveau = max(
            (NIVEAUX_LANGUE_ORDRE.get(v, 0) for v in profile.langues.values()),
            default=0,
        )
        # valeur_requise_numerique pour langue est stockée en équivalent IELTS (approximation)
        # simplification MVP : on considère B2 (=4) comme seuil pratique par défaut
        seuil = 4
        return meilleur_niveau >= seuil

    if tc == TypeCritere.EXPERIENCE:
        exp_requise = critere.valeur_requise_numerique or 0
        return (profile.annees_experience or 0) >= exp_requise

    if tc == TypeCritere.DOMAINE_ETUDE:
        # Critère qualitatif difficile à automatiser strictement en Phase 1.
        # On le considère "à valider manuellement" -> compté comme non-bloquant par défaut
        # si non éliminatoire, mais signalé à l'utilisateur.
        return bool(profile.domaine_etude)

    return False


def calculer_score(db: Session, profile: UserProfile, pays: str, type_demarche: str) -> ScoringResultat:
    criteres_db = (
        db.query(CountryCriteria)
        .filter(CountryCriteria.pays == pays, CountryCriteria.type_demarche == type_demarche)
        .all()
    )

    if not criteres_db:
        raise ValueError(f"Aucun critère trouvé pour {pays} / {type_demarche}")

    resultats: list[CritereResultat] = []
    poids_total = sum(c.poids for c in criteres_db)
    poids_obtenu = 0
    criteres_eliminatoires_manquants = []

    for critere in criteres_db:
        rempli = _evaluer_critere(critere, profile)
        valeur_user = _extraire_valeur_utilisateur(profile, critere.type_critere)

        resultats.append(CritereResultat(
            libelle=critere.libelle,
            type_critere=critere.type_critere.value,
            valeur_requise=critere.valeur_requise,
            valeur_utilisateur=valeur_user,
            rempli=rempli,
            eliminatoire=critere.eliminatoire,
            poids=critere.poids,
            explication=critere.explication,
        ))

        if rempli:
            poids_obtenu += critere.poids
        elif critere.eliminatoire:
            criteres_eliminatoires_manquants.append(critere.libelle)

    score_brut = round((poids_obtenu / poids_total) * 100, 1) if poids_total > 0 else 0.0
    eligible = len(criteres_eliminatoires_manquants) == 0
    tranche = _score_vers_tranche(score_brut, eligible)

    return ScoringResultat(
        pays=pays,
        type_demarche=type_demarche,
        score_brut=score_brut,
        tranche=tranche,
        eligible=eligible,
        criteres=resultats,
        criteres_manquants_eliminatoires=criteres_eliminatoires_manquants,
    )
