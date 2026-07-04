"""
Extraction de CV : PDF -> texte brut -> JSON structuré via LLM.

Le résultat vient ENRICHIR le profil déclaratif existant, jamais l'écraser
silencieusement : en cas de conflit (ex: âge différent), on garde le champ existant
si déjà déclaré manuellement, et on ne complète que les champs vides.
"""
import json
from typing import Optional

import pdfplumber
from groq import Groq

from app.config import get_settings

settings = get_settings()

EXTRACTION_SYSTEM_PROMPT = """Tu extrais des informations structurées d'un CV pour un outil \
d'évaluation d'éligibilité à l'immigration/aux bourses d'études.

RÈGLES :
- N'invente AUCUNE information absente du texte. Si une donnée n'est pas trouvable, mets null.
- Pour les langues, déduis un niveau CECRL (A1-C2) uniquement si explicitement mentionné \
(ex: "anglais courant" -> B2, "anglais natif" -> C2, "TOEFL 90" -> B2). Sinon null.
- Pour les années d'expérience, calcule la somme des périodes professionnelles mentionnées, \
pas juste la dernière.
- Réponds UNIQUEMENT en JSON valide, sans texte avant/après, sans balises markdown."""

EXTRACTION_SCHEMA_EXAMPLE = """{
  "niveau_diplome": "Master" | "Licence" | "Bac+2" | "Bac" | "Doctorat" | null,
  "domaine_etude": "string ou null",
  "etablissement": "string ou null",
  "annee_obtention": nombre ou null,
  "annees_experience": nombre décimal ou null,
  "secteur_activite": "string ou null",
  "poste_actuel": "string ou null",
  "langues": {"français": "C2", "anglais": "B1"} ou {},
  "age": nombre ou null,
  "confiance_extraction": "haute" | "moyenne" | "basse"
}"""


def extraire_texte_pdf(chemin_fichier: str) -> str:
    """Extrait le texte brut d'un fichier PDF."""
    texte_complet = []
    with pdfplumber.open(chemin_fichier) as pdf:
        for page in pdf.pages:
            texte_page = page.extract_text()
            if texte_page:
                texte_complet.append(texte_page)

    texte = "\n".join(texte_complet)
    if not texte.strip():
        raise ValueError(
            "Aucun texte extractible de ce PDF. Il s'agit probablement d'un scan/image "
            "sans couche texte — un CV texte natif (Word exporté en PDF) est nécessaire."
        )
    return texte


def extraire_donnees_structurees(texte_cv: str) -> dict:
    """Appelle le LLM pour structurer le texte du CV en JSON exploitable."""
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY non configurée — extraction CV impossible.")

    client = Groq(api_key=settings.GROQ_API_KEY)

    user_prompt = f"""Voici le texte extrait d'un CV. Structure-le selon ce schéma exact :
{EXTRACTION_SCHEMA_EXAMPLE}

Texte du CV :
---
{texte_cv[:8000]}
---"""
    # texte_cv tronqué à 8000 caractères par sécurité (limite de contexte raisonnable pour un CV)

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,  # basse température : on veut de l'extraction fidèle, pas de créativité
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)

    except json.JSONDecodeError as e:
        raise RuntimeError(f"Le LLM a retourné un JSON invalide : {e}")
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'appel au LLM d'extraction : {e}")


def fusionner_avec_profil_existant(donnees_cv: dict, profil_existant: dict) -> dict:
    """
    Fusionne les données extraites du CV avec le profil déclaratif existant.
    Priorité au profil déclaratif quand il existe déjà (l'utilisateur l'a dit lui-même),
    le CV ne comble que les trous.
    """
    resultat = dict(profil_existant)
    champs_fusionnables = [
        "niveau_diplome", "domaine_etude", "etablissement", "annee_obtention",
        "annees_experience", "secteur_activite", "poste_actuel", "age",
    ]

    for champ in champs_fusionnables:
        valeur_existante = resultat.get(champ)
        valeur_cv = donnees_cv.get(champ)
        if (valeur_existante is None or valeur_existante == "") and valeur_cv is not None:
            resultat[champ] = valeur_cv

    # Fusion spéciale pour les langues (dict) : on prend le niveau le plus élevé par langue
    langues_existantes = resultat.get("langues") or {}
    langues_cv = donnees_cv.get("langues") or {}
    niveaux_ordre = ["AUCUN", "A1", "A2", "B1", "B2", "C1", "C2"]

    langues_fusionnees = dict(langues_existantes)
    for langue, niveau_cv in langues_cv.items():
        niveau_existant = langues_fusionnees.get(langue)
        if niveau_existant is None:
            langues_fusionnees[langue] = niveau_cv
        else:
            try:
                if niveaux_ordre.index(niveau_cv) > niveaux_ordre.index(niveau_existant):
                    langues_fusionnees[langue] = niveau_cv
            except ValueError:
                pass  # niveau non reconnu, on garde l'existant

    resultat["langues"] = langues_fusionnees
    resultat["donnees_source"] = "mixte" if profil_existant else "cv"

    return resultat
