"""
Machine à états de la conversation WhatsApp : pose les questions une par une,
valide chaque réponse, et une fois le profil complet, enchaîne automatiquement
sur le scoring + coaching + checklist, réutilisant les services existants
(aucune logique métier dupliquée, seulement l'orchestration conversationnelle).
"""
from sqlalchemy.orm import Session

from app.models.conversation import ConversationState
from app.models.user import User, UserProfile
from app.services.scoring_service import calculer_score
from app.services.coach_service import generer_plan_coaching
from app.services.checklist_service import obtenir_checklist
from app.services.chat_service import poser_question

NIVEAUX_DIPLOME_VALIDES = {"bac": "Bac", "bac+2": "Bac+2", "licence": "Licence", "master": "Master", "doctorat": "Doctorat"}
NIVEAUX_LANGUE_VALIDES = {"a1", "a2", "b1", "b2", "c1", "c2"}
PAYS_VALIDES = {"canada": "Canada", "france": "France"}
DEMARCHES_VALIDES = {"1": "visa_etudiant", "2": "bourse", "visa": "visa_etudiant", "bourse": "bourse"}

# Ordre des étapes et question associée à chacune
ETAPES = [
    ("attente_age", "Quel âge as-tu ? (ex: 24)"),
    ("attente_diplome", "Quel est ton niveau de diplôme ? (Bac / Bac+2 / Licence / Master / Doctorat)"),
    ("attente_domaine", "Quel est ton domaine d'étude ? (ex: Informatique de Gestion)"),
    ("attente_experience", "Combien d'années d'expérience professionnelle as-tu ? (ex: 1.5, ou 0 si aucune)"),
    ("attente_langue_fr", "Ton niveau de français ? (A1 / A2 / B1 / B2 / C1 / C2)"),
    ("attente_langue_en", "Ton niveau d'anglais ? (A1 / A2 / B1 / B2 / C1 / C2)"),
    ("attente_capacite_financiere", "Quelle est ta capacité financière disponible, en FCFA ? (ex: 10000000)"),
    ("attente_pays", "Quel pays vises-tu ? (Canada / France)"),
    ("attente_demarche", "Quel type de démarche ? (1 = Visa étudiant / 2 = Bourse)"),
]
ETAPES_PAR_NOM = {nom: question for nom, question in ETAPES}


def _prochaine_etape(etape_actuelle: str) -> str:
    noms = [nom for nom, _ in ETAPES]
    if etape_actuelle == "debut":
        return noms[0]
    idx = noms.index(etape_actuelle)
    if idx + 1 < len(noms):
        return noms[idx + 1]
    return "termine"


def _valider_reponse(etape: str, texte: str) -> tuple[bool, str, str]:
    """
    Valide et normalise la réponse selon l'étape. Retourne (valide, valeur_normalisee, message_erreur).
    """
    texte = texte.strip()

    if etape == "attente_age":
        if texte.isdigit() and 15 <= int(texte) <= 80:
            return True, texte, ""
        return False, "", "Merci d'indiquer un âge valide (nombre entre 15 et 80)."

    if etape == "attente_diplome":
        niveau = NIVEAUX_DIPLOME_VALIDES.get(texte.lower())
        if niveau:
            return True, niveau, ""
        return False, "", "Merci de choisir parmi : Bac, Bac+2, Licence, Master, Doctorat."

    if etape == "attente_domaine":
        if len(texte) >= 2:
            return True, texte, ""
        return False, "", "Merci d'indiquer ton domaine d'étude."

    if etape == "attente_experience":
        try:
            valeur = float(texte.replace(",", "."))
            if 0 <= valeur <= 50:
                return True, str(valeur), ""
        except ValueError:
            pass
        return False, "", "Merci d'indiquer un nombre d'années valide (ex: 1.5 ou 0)."

    if etape in ("attente_langue_fr", "attente_langue_en"):
        if texte.lower() in NIVEAUX_LANGUE_VALIDES:
            return True, texte.upper(), ""
        return False, "", "Merci de choisir parmi : A1, A2, B1, B2, C1, C2."

    if etape == "attente_capacite_financiere":
        if texte.isdigit():
            return True, texte, ""
        return False, "", "Merci d'indiquer un montant en FCFA, en chiffres uniquement (ex: 10000000)."

    if etape == "attente_pays":
        pays = PAYS_VALIDES.get(texte.lower())
        if pays:
            return True, pays, ""
        return False, "", "Merci de choisir : Canada ou France."

    if etape == "attente_demarche":
        demarche = DEMARCHES_VALIDES.get(texte.lower())
        if demarche:
            return True, demarche, ""
        return False, "", "Merci de répondre 1 (Visa étudiant) ou 2 (Bourse)."

    return False, "", "Étape inconnue."


def _finaliser_profil(db: Session, numero: str, reponses: dict) -> str:
    """Crée/complète le User + UserProfile à partir des réponses collectées, puis calcule le résultat complet."""
    user = db.query(User).filter(User.whatsapp_number == numero).first()
    if not user:
        user = User(whatsapp_number=numero)
        db.add(user)
        db.flush()

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    donnees = {
        "age": int(reponses["attente_age"]),
        "niveau_diplome": reponses["attente_diplome"],
        "domaine_etude": reponses["attente_domaine"],
        "annees_experience": float(reponses["attente_experience"]),
        "langues": {"francais": reponses["attente_langue_fr"], "anglais": reponses["attente_langue_en"]},
        "capacite_financiere_fcfa": int(reponses["attente_capacite_financiere"]),
        "pays_cible": reponses["attente_pays"],
        "type_demarche": reponses["attente_demarche"],
    }

    if profile:
        for champ, valeur in donnees.items():
            setattr(profile, champ, valeur)
    else:
        profile = UserProfile(user_id=user.id, **donnees)
        db.add(profile)

    db.commit()
    db.refresh(profile)

    # Enchaîne directement sur scoring + coaching + checklist
    resultat_scoring = calculer_score(db, profile, donnees["pays_cible"], donnees["type_demarche"])
    plan_coaching = generer_plan_coaching(resultat_scoring)
    checklist = obtenir_checklist(db, donnees["pays_cible"], donnees["type_demarche"])

    return _formater_reponse_finale(resultat_scoring, plan_coaching, checklist)


def _formater_reponse_finale(resultat_scoring, plan_coaching, checklist) -> str:
    """Construit le message WhatsApp final à partir du score, du coaching et de la checklist."""
    emoji_tranche = {"Élevé": "🟢", "Moyen": "🟡", "Faible": "🔴"}.get(resultat_scoring.tranche, "⚪")

    lignes = [f"{emoji_tranche} *Chances estimées : {resultat_scoring.tranche}*", ""]

    if not resultat_scoring.eligible:
        lignes.append("⚠️ Critère(s) éliminatoire(s) manquant(s) : " + ", ".join(resultat_scoring.criteres_manquants_eliminatoires))
        lignes.append("")

    lignes.append("*Détail par critère :*")
    for c in resultat_scoring.criteres:
        statut = "✅" if c.rempli else "❌"
        lignes.append(f"{statut} {c.libelle}")
    lignes.append("")

    lignes.append("*🎯 Ton plan d'action :*")
    if plan_coaching.get("message_general"):
        lignes.append(plan_coaching["message_general"])
    for action in plan_coaching.get("actions", []):
        lignes.append(f"• {action['action']}")
    lignes.append("")

    lignes.append("*📄 Documents à préparer :*")
    for doc in checklist:
        tag = "🔴" if doc["obligatoire"] else "⚪"
        lignes.append(f"{tag} {doc['document']}")

    lignes.append("")
    lignes.append("_⚠️ Informations indicatives — vérifie toujours les exigences officielles à jour._")
    lignes.append("_Tape 'recommencer' pour refaire une évaluation._")
    lignes.append("_Tu peux aussi me poser directement une question sur ton dossier._")

    return "\n".join(lignes)


def traiter_message_entrant(db: Session, numero: str, texte_message: str) -> str:
    """
    Point d'entrée principal : fait progresser la conversation d'un utilisateur
    d'un message, et retourne le texte de la réponse à lui renvoyer.
    """
    texte_message = texte_message.strip()

    etat = db.query(ConversationState).filter(ConversationState.whatsapp_number == numero).first()

    # Commande de reset, disponible à tout moment
    if texte_message.lower() in ("recommencer", "reset", "restart"):
        if etat:
            db.delete(etat)
            db.commit()
        etat = ConversationState(whatsapp_number=numero, etape_courante=ETAPES[0][0], reponses_temporaires={})
        db.add(etat)
        db.commit()
        return (
            "👋 Bienvenue sur *Boussole* — l'agent qui évalue tes chances d'immigration/bourse "
            "(Canada 🇨🇦 et France 🇫🇷).\n\nCommençons : " + ETAPES[0][1]
        )

    if not etat:
        etat = ConversationState(whatsapp_number=numero, etape_courante=ETAPES[0][0], reponses_temporaires={})
        db.add(etat)
        db.commit()
        return (
            "👋 Bienvenue sur *Boussole* — l'agent qui évalue tes chances d'immigration/bourse "
            "(Canada 🇨🇦 et France 🇫🇷).\n\nCommençons : " + ETAPES[0][1]
        )

    if etat.etape_courante == "termine":
        # Une fois l'évaluation faite, tout message libre (hors 'recommencer', déjà géré
        # plus haut) est traité comme une question au chatbot, ancré sur le profil déjà
        # enregistré de cet utilisateur.
        user = db.query(User).filter(User.whatsapp_number == numero).first()
        if not user:
            return "Erreur : profil introuvable. Tape 'recommencer' pour refaire une évaluation."
        return poser_question(db, user.id, texte_message)

    # Valide la réponse à l'étape courante
    valide, valeur_normalisee, message_erreur = _valider_reponse(etat.etape_courante, texte_message)
    if not valide:
        return f"⚠️ {message_erreur}"

    reponses = dict(etat.reponses_temporaires or {})
    reponses[etat.etape_courante] = valeur_normalisee
    etat.reponses_temporaires = reponses

    etape_suivante = _prochaine_etape(etat.etape_courante)
    etat.etape_courante = etape_suivante
    db.commit()

    if etape_suivante == "termine":
        try:
            return _finaliser_profil(db, numero, reponses)
        except Exception as e:
            print(f"❌ Erreur lors de la finalisation du profil pour {numero} : {e}")
            return (
                "❌ Une erreur est survenue pendant le calcul de ton évaluation. "
                "Tape 'recommencer' pour réessayer."
            )

    return ETAPES_PAR_NOM[etape_suivante]
