"""
Coach IA : transforme un ScoringResultat en plan d'action concret et priorisé.

Approche en deux temps :
1. Un tri déterministe (sans LLM) des critères manquants par poids décroissant
   -> garantit que le plan est toujours cohérent et reproductible, même si le LLM est indisponible.
2. Un appel LLM optionnel pour reformuler chaque action en langage naturel motivant
   et estimer un ordre de grandeur de délai. Si le LLM échoue, on retombe sur le plan
   déterministe brut (dégradation gracieuse, pas de plantage).
"""
import json
from dataclasses import dataclass
from typing import Optional

from groq import Groq

from app.config import get_settings
from app.services.scoring_service import ScoringResultat, CritereResultat

settings = get_settings()


@dataclass
class ActionCoaching:
    action: str
    impact_estime: str  # "Fort", "Moyen", "Faible" - dérivé du poids du critère
    critere_lie: str


SYSTEM_PROMPT = """Tu es un conseiller en immigration factuel et prudent, spécialisé dans les démarches \
depuis le Sénégal vers le Canada et la France (visa étudiant, bourses).

RÈGLES STRICTES :
- Tu reformules des actions déjà déterminées, tu n'inventes JAMAIS de nouveaux critères.
- Reste concret et actionnable ("Passe le test IELTS et vise 6.0" plutôt que "Améliore ton anglais").
- Ne donne jamais de garantie de résultat ("tu seras accepté à 100%").
- Précise systématiquement que les démarches officielles doivent être vérifiées sur les sites \
officiels (Campus France, IRCC).
- Réponds UNIQUEMENT en JSON valide, sans texte avant/après, sans balises markdown."""


def _construire_actions_deterministes(scoring: ScoringResultat) -> list[ActionCoaching]:
    """Trie les critères non remplis par poids décroissant -> priorité d'impact."""
    manquants = [c for c in scoring.criteres if not c.rempli]
    manquants.sort(key=lambda c: c.poids, reverse=True)

    actions = []
    for c in manquants:
        if c.poids >= 20:
            impact = "Fort"
        elif c.poids >= 10:
            impact = "Moyen"
        else:
            impact = "Faible"
        actions.append(ActionCoaching(
            action=f"{c.libelle} — requis : {c.valeur_requise}",
            impact_estime=impact,
            critere_lie=c.libelle,
        ))
    return actions


def _appeler_llm_reformulation(actions: list[ActionCoaching], scoring: ScoringResultat) -> Optional[list[dict]]:
    """Reformule les actions brutes en conseils motivants et clairs. Retourne None si échec."""
    if not settings.GROQ_API_KEY:
        return None

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)

        actions_brutes = [
            {"action": a.action, "impact": a.impact_estime, "critere": a.critere_lie}
            for a in actions
        ]

        user_prompt = f"""Contexte : candidature {scoring.type_demarche} pour {scoring.pays}.
Score actuel (usage interne uniquement, ne pas répéter le chiffre à l'utilisateur) : {scoring.score_brut}/100.

Actions à reformuler (garde exactement les mêmes actions, dans le même ordre, reformule juste le texte) :
{json.dumps(actions_brutes, ensure_ascii=False, indent=2)}

Réponds avec un JSON de cette forme exacte :
{{
  "actions": [
    {{"action": "texte reformulé, concret et motivant", "impact": "Fort/Moyen/Faible", "delai_estime": "ex: 2-3 mois"}}
  ],
  "message_general": "1-2 phrases d'encouragement réaliste, sans garantie de résultat"
}}"""

        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        # Dégradation gracieuse : on log et on retombe sur le plan déterministe
        print(f"⚠️ Échec reformulation LLM coach : {e}")
        return None


def generer_plan_coaching(scoring: ScoringResultat) -> dict:
    """
    Point d'entrée principal. Retourne toujours un plan utilisable,
    que le LLM soit disponible ou non.
    """
    actions_deterministes = _construire_actions_deterministes(scoring)

    if not actions_deterministes:
        return {
            "actions": [],
            "message_general": (
                "Tu remplis déjà tous les critères identifiés pour cette démarche. "
                "Vérifie néanmoins les informations les plus récentes sur le site officiel "
                "avant de déposer ton dossier, les exigences évoluent régulièrement."
            ),
        }

    reformulation = _appeler_llm_reformulation(actions_deterministes, scoring)

    if reformulation and "actions" in reformulation:
        return reformulation

    # Fallback déterministe si le LLM n'a pas répondu correctement
    return {
        "actions": [
            {"action": a.action, "impact": a.impact_estime, "delai_estime": "À évaluer"}
            for a in actions_deterministes
        ],
        "message_general": (
            "Voici les points à améliorer en priorité, du plus impactant au moins impactant. "
            "Vérifie chaque exigence sur le site officiel avant de te lancer."
        ),
    }
