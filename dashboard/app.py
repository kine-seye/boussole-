"""
Dashboard Streamlit pour Boussole.

Interface simple en 3 étapes : profil (+ upload CV optionnel) -> score -> checklist.
Consomme l'API FastAPI déjà en place, ne duplique aucune logique métier.
"""
import streamlit as st
import requests
import os


def _obtenir_api_url() -> str:
    """
    Priorité : Streamlit Secrets (production) > variable d'environnement > localhost (dev local).
    st.secrets peut lever une exception si aucun fichier secrets.toml n'existe -> on l'attrape.
    """
    try:
        if "BOUSSOLE_API_URL" in st.secrets:
            return st.secrets["BOUSSOLE_API_URL"]
    except Exception:
        pass
    return os.getenv("BOUSSOLE_API_URL", "http://localhost:8000")


API_URL = _obtenir_api_url()

st.set_page_config(page_title="Boussole", page_icon="🧭", layout="centered")

# --- État de session ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "resultat_scoring" not in st.session_state:
    st.session_state.resultat_scoring = None

st.title("🧭 Boussole")
st.caption("Évalue tes chances d'immigration ou de bourse — Canada & France")

PAYS_DISPONIBLES = ["Canada", "France"]
DEMARCHES_DISPONIBLES = {"Visa étudiant": "visa_etudiant", "Bourse d'études": "bourse"}
NIVEAUX_DIPLOME = ["Bac", "Bac+2", "Licence", "Master", "Doctorat"]
NIVEAUX_LANGUE = ["AUCUN", "A1", "A2", "B1", "B2", "C1", "C2"]


def appeler_api(methode: str, endpoint: str, **kwargs):
    """Wrapper simple avec gestion d'erreur lisible pour l'utilisateur."""
    try:
        reponse = requests.request(methode, f"{API_URL}{endpoint}", timeout=30, **kwargs)
        reponse.raise_for_status()
        return reponse.json(), None
    except requests.exceptions.ConnectionError:
        return None, "❌ Impossible de joindre le serveur. Vérifie que `uvicorn` tourne bien sur le port 8000."
    except requests.exceptions.HTTPError as e:
        try:
            detail = reponse.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"❌ Erreur : {detail}"
    except Exception as e:
        return None, f"❌ Erreur inattendue : {e}"


# ============================================================
# ÉTAPE 1 — PROFIL
# ============================================================
st.header("1. Ton profil")

with st.form("form_profil"):
    col1, col2 = st.columns(2)
    with col1:
        whatsapp = st.text_input("Numéro WhatsApp (identifiant)", placeholder="221771234567")
        age = st.number_input("Âge", min_value=15, max_value=80, value=25)
        niveau_diplome = st.selectbox("Niveau de diplôme", NIVEAUX_DIPLOME, index=2)
        domaine_etude = st.text_input("Domaine d'étude", placeholder="Informatique de Gestion")
    with col2:
        annees_experience = st.number_input("Années d'expérience", min_value=0.0, max_value=50.0, value=1.0, step=0.5)
        capacite_financiere = st.number_input("Capacité financière (FCFA)", min_value=0, value=10_000_000, step=500_000)
        niveau_anglais = st.selectbox("Niveau d'anglais", NIVEAUX_LANGUE, index=4)
        niveau_francais = st.selectbox("Niveau de français", NIVEAUX_LANGUE, index=6)

    st.markdown("**Ta cible**")
    col3, col4 = st.columns(2)
    with col3:
        pays_cible = st.selectbox("Pays visé", PAYS_DISPONIBLES)
    with col4:
        demarche_label = st.selectbox("Type de démarche", list(DEMARCHES_DISPONIBLES.keys()))

    submit_profil = st.form_submit_button("🎯 Enregistrer mon profil et évaluer mes chances", use_container_width=True)

if submit_profil:
    if not whatsapp:
        st.error("Le numéro WhatsApp est requis pour identifier ton profil.")
    else:
        payload = {
            "whatsapp_number": whatsapp,
            "age": int(age),
            "niveau_diplome": niveau_diplome,
            "domaine_etude": domaine_etude or None,
            "annees_experience": float(annees_experience),
            "langues": {"anglais": niveau_anglais, "francais": niveau_francais},
            "capacite_financiere_fcfa": int(capacite_financiere),
            "pays_cible": pays_cible,
            "type_demarche": DEMARCHES_DISPONIBLES[demarche_label],
        }
        with st.spinner("Enregistrement du profil..."):
            resultat, erreur = appeler_api("POST", "/profile", json=payload)

        if erreur:
            st.error(erreur)
        else:
            st.session_state.user_id = resultat["user_id"]
            st.success("✅ Profil enregistré !")

            # Enchaîne directement sur le calcul du score, pour éviter tout résultat
            # périmé et supprimer l'étape manuelle en double.
            with st.spinner("Calcul de tes chances en cours..."):
                resultat_score, erreur_score = appeler_api(
                    "POST", "/score",
                    json={
                        "user_id": st.session_state.user_id,
                        "pays": pays_cible,
                        "type_demarche": DEMARCHES_DISPONIBLES[demarche_label],
                    },
                )
            if erreur_score:
                st.error(erreur_score)
            else:
                st.session_state.resultat_scoring = resultat_score

# ============================================================
# ÉTAPE 1bis — UPLOAD CV (optionnel, enrichit le profil)
# ============================================================
if st.session_state.user_id:
    with st.expander("📄 Enrichir mon profil avec mon CV (PDF, optionnel)"):
        fichier_cv = st.file_uploader("Choisis ton CV au format PDF", type=["pdf"])
        if fichier_cv and st.button("Analyser mon CV"):
            with st.spinner("Analyse du CV en cours..."):
                fichiers = {"fichier": (fichier_cv.name, fichier_cv.getvalue(), "application/pdf")}
                resultat, erreur = appeler_api(
                    "POST", f"/cv/upload?user_id={st.session_state.user_id}", files=fichiers
                )
            if erreur:
                st.error(erreur)
            else:
                st.success("✅ CV analysé et profil enrichi !")
                st.json(resultat["donnees_extraites"])

# ============================================================
# ÉTAPE 2 — SCORE
# ============================================================
if st.session_state.user_id:
    st.header("2. Tes chances")

if st.session_state.resultat_scoring:
    r = st.session_state.resultat_scoring

    couleurs_tranche = {"Élevé": "🟢", "Moyen": "🟡", "Faible": "🔴"}
    emoji = couleurs_tranche.get(r["tranche"], "⚪")

    st.subheader(f"{emoji} Chances estimées : {r['tranche']}")

    if not r["eligible"]:
        st.warning(
            "⚠️ Au moins un critère éliminatoire n'est pas rempli : "
            + ", ".join(r["criteres_manquants_eliminatoires"])
        )

    st.markdown("**Détail par critère :**")
    for c in r["criteres"]:
        statut = "✅" if c["rempli"] else "❌"
        eliminatoire_tag = " *(éliminatoire)*" if c["eliminatoire"] else ""
        with st.container():
            st.markdown(f"{statut} **{c['libelle']}**{eliminatoire_tag}")
            st.caption(f"Requis : {c['valeur_requise']} — Toi : {c['valeur_utilisateur'] or 'non renseigné'}")
            if c["explication"]:
                st.caption(f"ℹ️ {c['explication']}")

    st.markdown("---")
    st.subheader("🎯 Ton plan d'action")
    plan = r["plan_coaching"]
    if plan.get("message_general"):
        st.info(plan["message_general"])
    for action in plan.get("actions", []):
        impact = action.get("impact", "Moyen")
        icone_impact = {"Fort": "🔥", "Moyen": "⚡", "Faible": "💡"}.get(impact, "⚡")
        delai = action.get("delai_estime", "")
        st.markdown(f"{icone_impact} **{action['action']}**" + (f" _(≈ {delai})_" if delai else ""))

    st.caption(
        "⚠️ Ces informations sont indicatives. Vérifie toujours les exigences à jour "
        "sur le site officiel avant toute démarche (ambassade, Campus France, IRCC)."
    )

# ============================================================
# ÉTAPE 3 — CHECKLIST DOCUMENTS
# ============================================================
if st.session_state.resultat_scoring:
    st.header("3. Documents à préparer")
    resultat_checklist, erreur = appeler_api(
        "GET", f"/checklist?pays={pays_cible}&type_demarche={DEMARCHES_DISPONIBLES[demarche_label]}"
    )
    if erreur:
        st.error(erreur)
    else:
        for doc in resultat_checklist["documents"]:
            obligatoire_tag = "🔴 Obligatoire" if doc["obligatoire"] else "⚪ Optionnel"
            st.markdown(f"**{doc['document']}** — {obligatoire_tag}")
            if doc["delai_obtention_estime"]:
                st.caption(f"⏱️ Délai estimé : {doc['delai_obtention_estime']}")
            if doc["remarque"]:
                st.caption(f"💡 {doc['remarque']}")
            st.markdown("")
