"""
Chatbot conversationnel : répond aux questions libres de l'utilisateur, mais toujours
ancré sur les données réelles (profil, critères d'éligibilité, checklist documentaire)
déjà en base — jamais un LLM livré à lui-même sur un sujet aussi sensible que
l'immigration, où une hallucination (mauvais délai, mauvais montant) a de vraies
conséquences pour l'utilisateur.
"""
import json

from groq import Groq
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.chat import ChatMessage
from app.models.user import User, UserProfile
from app.models.criteria import CountryCriteria, DocumentChecklist

settings = get_settings()

NB_MESSAGES_HISTORIQUE = 10  # nombre de tours précédents à inclure comme contexte

SYSTEM_PROMPT = """Tu es l'assistant conversationnel de Boussole, une application qui aide des \
candidats sénégalais à évaluer leurs chances d'obtenir un visa étudiant ou une bourse (Canada, France).

RÈGLE LA PLUS IMPORTANTE — DISTINCTION OBLIGATOIRE DES SOURCES :
Tu dois TOUJOURS distinguer clairement deux types d'informations dans ta réponse :
1. Ce qui vient du CONTEXTE fourni ci-dessous (profil, critères, checklist) — c'est vérifié et fiable.
2. Ce qui vient de ta connaissance générale (noms d'universités, montants de frais de visa non \
listés dans le contexte, délais non précisés, etc.) — ce n'est PAS vérifié par Boussole.

Pour TOUTE information de type 2 (pas dans le contexte), tu DOIS :
- Soit refuser de donner un chiffre précis et rediriger vers la source officielle.
- Soit, si tu donnes quand même une réponse générale utile (ex: noms d'universités connues), \
  terminer explicitement cette partie par : "⚠️ Info non vérifiée dans la base Boussole — \
  confirme sur le site officiel avant de t'y fier."
Ne donne JAMAIS un chiffre précis (montant en CAD/EUR/FCFA, délai en semaines/mois) qui n'est pas \
explicitement présent dans le CONTEXTE, sans ce marqueur d'avertissement. C'est une règle stricte, \
pas une suggestion : un montant faux présenté avec assurance peut avoir de vraies conséquences \
pour l'utilisateur sur un sujet d'immigration.

AUTRES RÈGLES :
- Tu ne réponds QU'à partir des informations fournies dans le contexte pour tout ce qui concerne \
son propre dossier (ses critères, sa checklist). Tu n'inventes JAMAIS un chiffre, un délai, ou \
une condition qui n'est pas dans ce contexte pour SA situation personnelle.
- Reste concis (3-5 phrases maximum sauf si la question demande explicitement plus de détail).
- Ton chaleureux mais factuel, jamais de fausses promesses sur les chances de réussite.
- Tu peux discuter du contenu du profil de l'utilisateur, des critères, de la checklist, et donner \
des conseils généraux de méthode (comment bien préparer un dossier), mais jamais de conseil \
juridique personnalisé engageant."""


def _construire_contexte(db: Session, user_id) -> str:
    """Rassemble tout ce que le chatbot est autorisé à savoir : profil + critères + checklist
    pertinents pour le pays/démarche ciblés par l'utilisateur, s'il en a un."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if not profile:
        return "Aucun profil enregistré pour cet utilisateur pour l'instant."

    profil_dict = {
        "age": profile.age,
        "niveau_diplome": profile.niveau_diplome,
        "domaine_etude": profile.domaine_etude,
        "annees_experience": profile.annees_experience,
        "langues": profile.langues,
        "capacite_financiere_fcfa": profile.capacite_financiere_fcfa,
        "pays_cible": profile.pays_cible,
        "type_demarche": profile.type_demarche,
    }
    profil_json = json.dumps(profil_dict, ensure_ascii=False, indent=2)
    morceaux = [f"PROFIL DE L'UTILISATEUR :\n{profil_json}"]

    if profile.pays_cible and profile.type_demarche:
        criteres = (
            db.query(CountryCriteria)
            .filter(CountryCriteria.pays == profile.pays_cible, CountryCriteria.type_demarche == profile.type_demarche)
            .all()
        )
        morceaux.append("CRITÈRES D'ÉLIGIBILITÉ POUR SA CIBLE :\n" + "\n".join(
            f"- {c.libelle} : {c.valeur_requise} (poids {c.poids}, éliminatoire={c.eliminatoire}) — {c.explication or ''}"
            for c in criteres
        ))

        documents = (
            db.query(DocumentChecklist)
            .filter(DocumentChecklist.pays == profile.pays_cible, DocumentChecklist.type_demarche == profile.type_demarche)
            .order_by(DocumentChecklist.ordre_affichage)
            .all()
        )
        morceaux.append("DOCUMENTS REQUIS POUR SA CIBLE :\n" + "\n".join(
            f"- {d.document} ({'obligatoire' if d.obligatoire else 'optionnel'}, délai estimé: {d.delai_obtention_estime or 'non précisé'})"
            for d in documents
        ))

    return "\n\n".join(morceaux)


def poser_question(db: Session, user_id, question: str) -> str:
    """
    Point d'entrée principal : traite une question libre de l'utilisateur, en s'appuyant
    sur son historique de conversation et le contexte de son profil/critères/checklist.
    Persiste les deux messages (utilisateur + assistant) en base avant de retourner.
    """
    if not settings.GROQ_API_KEY:
        return (
            "Le chatbot n'est pas encore configuré (clé Groq manquante). "
            "Contacte l'administrateur de l'application."
        )

    contexte = _construire_contexte(db, user_id)

    historique = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(NB_MESSAGES_HISTORIQUE)
        .all()
    )
    historique = list(reversed(historique))  # remet dans l'ordre chronologique

    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\nCONTEXTE :\n" + contexte}]
    for m in historique:
        messages.append({"role": m.role, "content": m.contenu})
    messages.append({"role": "user", "content": question})

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.3,
        )
        reponse_texte = response.choices[0].message.content
    except Exception as e:
        print(f"❌ Erreur chatbot Groq pour {user_id} : {e}")
        reponse_texte = (
            "Désolé, une erreur est survenue en essayant de répondre. Réessaie dans un instant."
        )

    # Persiste les deux messages, y compris en cas d'erreur (pour garder une trace cohérente)
    db.add(ChatMessage(user_id=user_id, role="user", contenu=question))
    db.add(ChatMessage(user_id=user_id, role="assistant", contenu=reponse_texte))
    db.commit()

    return reponse_texte


def obtenir_historique(db: Session, user_id) -> list[dict]:
    """Retourne l'historique complet des messages d'un utilisateur, dans l'ordre chronologique."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [{"role": m.role, "contenu": m.contenu, "created_at": m.created_at.isoformat()} for m in messages]
