"""
Dashboard Streamlit pour Boussole — identité visuelle "instrument de navigation".

Palette : indigo profond (#12213D), papier chaud (#FBF8F2), laiton (#B98A2E),
sarcelle/ambre/brique pour les 3 tranches de chances (Élevé/Moyen/Faible).
Typographie : Fraunces (titres) + Work Sans (corps) + IBM Plex Mono (données).
Signature : cadran de boussole en SVG pour visualiser le score, au lieu d'un badge coloré.
"""
import streamlit as st
import requests
import os


def html(chaine: str) -> str:
    """Nettoie un bloc HTML multi-lignes avant de le passer à st.markdown.
    Deux pièges Markdown corrigés ici :
    1. Toute ligne indentée de 4+ espaces est traitée comme un bloc de code brut
       (non interprété) -> on retire l'indentation de CHAQUE ligne.
    2. Une ligne vide au milieu du bloc termine prématurément le "bloc HTML" au sens
       CommonMark, faisant retomber la suite en parsing Markdown normal (d'où des
       balises visibles en texte brut) -> on retire aussi les lignes vides résiduelles
       (ex: quand une valeur optionnelle interpolée est une chaîne vide)."""
    lignes = (ligne.lstrip() for ligne in chaine.strip().split("\n"))
    return "\n".join(ligne for ligne in lignes if ligne)


def _obtenir_api_url() -> str:
    """Priorité : Streamlit Secrets (production) > variable d'environnement > localhost (dev local)."""
    try:
        if "BOUSSOLE_API_URL" in st.secrets:
            return st.secrets["BOUSSOLE_API_URL"]
    except Exception:
        pass
    return os.getenv("BOUSSOLE_API_URL", "http://localhost:8000")


API_URL = _obtenir_api_url()

st.set_page_config(page_title="Boussole", page_icon="🧭", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Work+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap');

:root {
    --ink: #12213D;
    --paper: #FBF8F2;
    --brass: #B98A2E;
    --brass-light: #E4C883;
    --teal: #1F6F5C;
    --amber: #D6A23B;
    --brick: #B4432F;
    --ink-muted: #5B6472;
    --border-soft: rgba(18, 33, 61, 0.12);
}

.stApp { background: var(--paper) !important; }

html, body, [class*="css"] { font-family: 'Work Sans', sans-serif; color: var(--ink) !important; }
h1, h2, h3, h4, h5, h6 { font-family: 'Fraunces', serif !important; color: var(--ink) !important; letter-spacing: -0.01em; }
p, span, div, label { color: var(--ink) !important; }
.mono { font-family: 'IBM Plex Mono', monospace; }

#MainMenu, footer {visibility: hidden;}

.boussole-hero {
    display: flex; align-items: center; gap: 1.1rem;
    padding: 1.6rem 0 0.4rem 0; border-bottom: 1px solid var(--border-soft); margin-bottom: 1.6rem;
}
.boussole-hero-icon { width: 52px; height: 52px; flex-shrink: 0; }
.boussole-hero-title { font-family: 'Fraunces', serif; font-size: 2rem; font-weight: 700; color: var(--ink) !important; line-height: 1; margin: 0; }
.boussole-hero-tagline { color: var(--ink-muted) !important; font-size: 0.98rem; margin-top: 0.35rem; }

.boussole-steps { display: flex; gap: 0.5rem; margin-bottom: 1.8rem; }
.boussole-step {
    flex: 1; padding: 0.6rem 0.9rem; border-radius: 10px; background: white;
    border: 1px solid var(--border-soft); font-size: 0.82rem; color: var(--ink-muted) !important;
}
.boussole-step.actif, .boussole-step.actif * { background: var(--ink); border-color: var(--ink); color: var(--paper) !important; }
.boussole-step-num { font-family: 'IBM Plex Mono', monospace; font-weight: 500; opacity: 0.6; margin-right: 0.4rem; }

.boussole-card {
    background: white; border: 1px solid var(--border-soft); border-radius: 14px;
    padding: 1.4rem 1.6rem; margin-bottom: 1.2rem;
}
.boussole-card-brass { border-left: 3px solid var(--brass); }

.critere-ligne {
    padding: 1rem 1.2rem;
    border-radius: 8px;
    background-color: #FFFFFF; /* Fond blanc pour détacher du fond crème */
    border: 1px solid var(--border-soft);
    margin-bottom: 0.8rem; /* Espace entre les critères */
    transition: all 0.2s ease;
}

/* Effet au survol pour rendre l'application interactive */
.critere-ligne:hover {
    border-color: var(--brass); /* Le laiton s'active au survol */
    transform: translateX(4px); /* Léger décalage dynamique */
}
.critere-ligne:last-child { border-bottom: none; }
.critere-titre { font-weight: 600; font-size: 0.96rem; color: var(--ink) !important; }
.critere-detail {
    font-family: 'Work Sans', sans-serif;
    color: var(--ink-muted) !important;
    font-size: 0.88rem;
    margin-top: 0.35rem;
    background: var(--paper); /* Un léger fond contrasté */
    padding: 0.25rem 0.6rem;
    border-radius: 5px;
    display: inline-block; /* Pour ne pas prendre toute la largeur */
}
.critere-explication { color: var(--ink-muted) !important; font-size: 0.82rem; margin-top: 0.25rem; font-style: italic; }
.tag-eliminatoire {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--brick) !important;
    background: rgba(180, 67, 47, 0.1); /* Fond rouge très léger */
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    margin-left: 0.6rem;
    font-weight: 600;
    vertical-align: middle;
}

.action-coaching { display: flex; gap: 0.7rem; align-items: flex-start; padding: 0.6rem 0; }
.action-coaching span { color: var(--ink) !important; }
.action-impact {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; text-transform: uppercase;
    letter-spacing: 0.04em; padding: 0.15rem 0.5rem; border-radius: 5px; flex-shrink: 0; margin-top: 0.15rem;
}
.impact-fort { background: rgba(180,67,47,0.12); color: var(--brick) !important; }
.impact-moyen { background: rgba(214,162,59,0.15); color: #8a6420 !important; }
.impact-faible { background: rgba(31,111,92,0.12); color: var(--teal) !important; }

.doc-ligne { display: flex; justify-content: space-between; align-items: baseline; padding: 0.7rem 0; border-bottom: 1px solid var(--border-soft); }
.doc-ligne:last-child { border-bottom: none; }
.doc-nom { font-weight: 600; font-size: 0.92rem; color: var(--ink) !important; }
.doc-tag { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 600; padding: 0.15rem 0.55rem; border-radius: 5px; white-space: nowrap; }
.doc-obligatoire { background: rgba(180,67,47,0.1); color: var(--brick) !important; }
.doc-optionnel { background: rgba(91,100,114,0.1); color: var(--ink-muted) !important; }
.doc-remarque { color: var(--ink-muted) !important; font-size: 0.8rem; margin-top: 0.2rem; }

/* 1. Cibler TOUS les boutons (Classiques et Formulaires) */
.stButton > button, 
.stFormSubmitButton > button {
    background: var(--brass) !important; 
    border-radius: 10px !important;
    border: none !important; 
    font-weight: 600 !important; 
    padding: 0.65rem 1.2rem !important; 
    transition: background 0.2s ease, transform 0.1s ease;
}

/* 2. Effet au survol global */
.stButton > button:hover, 
.stFormSubmitButton > button:hover {
    background: var(--brass-light) !important;
    opacity: 1 !important; /* On remplace l'ancienne opacité par un comportement propre */
}

/* 3. Effet au clic global */
.stButton > button:active, 
.stFormSubmitButton > button:active {
    transform: scale(0.98);
}

/* 4. Forcer la couleur du texte en blanc pur pour un contraste parfait */
.stButton > button *, 
.stFormSubmitButton > button * {
    color: #FFFFFF !important;
}

/* 5. Optionnel : repasser le texte en indigo au survol si le fond laiton s'éclaircit */
.stButton > button:hover *, 
.stFormSubmitButton > button:hover * {
    color: var(--ink) !important;
}

/* Widgets de formulaire : le thème sombre peut persister sur ces composants même
   quand le fond général de page est clair -> on force fond blanc + texte lisible. */
input, textarea, select {
    background-color: #FFFFFF !important;
    color: var(--ink) !important;
}
[data-baseweb="select"] > div,
[data-baseweb="input"] > div {
    background-color: #FFFFFF !important;
    color: var(--ink) !important;
    border-color: var(--border-soft) !important;
}
[data-baseweb="select"] *,
[data-baseweb="input"] * {
    color: var(--ink) !important;
}
[data-baseweb="popover"], [data-baseweb="menu"] {
    background-color: #FFFFFF !important;
}
li[role="option"] {
    background-color: #FFFFFF !important;
    color: var(--ink) !important;
}
li[role="option"]:hover, li[aria-selected="true"] {
    background-color: rgba(185, 138, 46, 0.15) !important;
}
.stNumberInput button {
    background-color: #FFFFFF !important;
    color: var(--ink) !important;
}
.stButton > button,
.stButton > button div,
.stButton > button p,
.stButton > button span {
    color: var(--paper) !important;
}
[data-testid*="FileUploader"] section {
    background-color: #FFFFFF !important;
    border: 1px dashed var(--border-soft) !important;
}
[data-testid*="FileUploader"] section * {
    color: var(--ink-muted) !important;
}
</style>
""", unsafe_allow_html=True)


def cadran_boussole(tranche: str) -> str:
    """
    SVG du cadran de boussole - signature visuelle de l'app.
    Trois zones colorées (Faible/Moyen/Élevé), aiguille pointant vers la tranche active.
    Volontairement 3 positions discrètes (pas un curseur continu) : on n'affiche jamais
    un score numérique précis à l'utilisateur, seulement la tranche qualitative.
    """
    positions_aiguille = {
        "Faible": (43.7, 67.5),
        "Moyen": (100.0, 35.0),
        "Élevé": (156.3, 67.5),
    }
    tip_x, tip_y = positions_aiguille.get(tranche, (100.0, 35.0))

    return html(f"""
    <svg viewBox="0 0 200 130" style="width:100%; max-width:320px; display:block; margin:0 auto;">
        <path d="M 100,100 L 20.0,100.0 A 80,80 0 0 1 60.0,30.7 Z" fill="#B4432F" opacity="0.85"/>
        <path d="M 100,100 L 60.0,30.7 A 80,80 0 0 1 140.0,30.7 Z" fill="#D6A23B" opacity="0.85"/>
        <path d="M 100,100 L 140.0,30.7 A 80,80 0 0 1 180.0,100.0 Z" fill="#1F6F5C" opacity="0.85"/>
        <circle cx="100" cy="100" r="82" fill="none" stroke="#12213D" stroke-width="1.5" opacity="0.15"/>
        <line x1="100" y1="100" x2="{tip_x}" y2="{tip_y}" stroke="#12213D" stroke-width="3.5" stroke-linecap="round"/>
        <circle cx="100" cy="100" r="7" fill="#12213D"/>
        <text x="20" y="118" font-family="Work Sans" font-size="9" fill="#5B6472">Faible</text>
        <text x="82" y="24" font-family="Work Sans" font-size="9" fill="#5B6472">Moyen</text>
        <text x="158" y="118" font-family="Work Sans" font-size="9" fill="#5B6472">Élevé</text>
    </svg>
    """)


if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "resultat_scoring" not in st.session_state:
    st.session_state.resultat_scoring = None

PAYS_DISPONIBLES = ["Canada", "France"]
DEMARCHES_DISPONIBLES = {"Visa étudiant": "visa_etudiant", "Bourse d'études": "bourse"}
NIVEAUX_DIPLOME = ["Bac", "Bac+2", "Licence", "Master", "Doctorat"]
NIVEAUX_LANGUE = ["AUCUN", "A1", "A2", "B1", "B2", "C1", "C2"]


def appeler_api(methode: str, endpoint: str, **kwargs):
    """
    Wrapper simple avec gestion d'erreur lisible pour l'utilisateur.
    Timeout élevé (60s) car le backend Render (plan gratuit) peut être en veille
    et mettre jusqu'à 50s à se réveiller sur la première requête.
    """
    try:
        reponse = requests.request(methode, f"{API_URL}{endpoint}", timeout=60, **kwargs)
        reponse.raise_for_status()
        return reponse.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Impossible de joindre le serveur. Vérifie que le backend est bien démarré."
    except requests.exceptions.Timeout:
        return None, "Le serveur met du temps à répondre (réveil après inactivité). Réessaie dans quelques secondes."
    except requests.exceptions.HTTPError as e:
        try:
            detail = reponse.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Erreur : {detail}"
    except Exception as e:
        return None, f"Erreur inattendue : {e}"


st.markdown(html("""
<div class="boussole-hero">
    <svg class="boussole-hero-icon" viewBox="0 0 52 52">
        <circle cx="26" cy="26" r="24" fill="none" stroke="#12213D" stroke-width="2"/>
        <circle cx="26" cy="26" r="24" fill="none" stroke="#B98A2E" stroke-width="1" opacity="0.4"/>
        <polygon points="26,10 30,26 26,42 22,26" fill="#12213D"/>
        <polygon points="26,10 30,26 26,26" fill="#B98A2E"/>
        <circle cx="26" cy="26" r="3" fill="#B98A2E"/>
    </svg>
    <div>
        <p class="boussole-hero-title">Boussole</p>
        <p class="boussole-hero-tagline">Ton copilote pour réussir tes démarches d'immigration et de bourses — Canada & France</p>
    </div>
</div>
"""), unsafe_allow_html=True)

etape_1_active = "actif" if not st.session_state.resultat_scoring else ""
etape_2_active = "actif" if st.session_state.resultat_scoring else ""

st.markdown(html(f"""
<div class="boussole-steps">
    <div class="boussole-step {etape_1_active}"><span class="boussole-step-num">01</span>Ton profil</div>
    <div class="boussole-step {etape_2_active}"><span class="boussole-step-num">02</span>Tes chances</div>
    <div class="boussole-step {etape_2_active}"><span class="boussole-step-num">03</span>Documents</div>
</div>
"""), unsafe_allow_html=True)

st.markdown('<div class="boussole-card">', unsafe_allow_html=True)
st.markdown("##### Parle-moi de toi")
st.caption("Ces informations restent privées et servent uniquement à évaluer tes chances.")

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

    submit_profil = st.form_submit_button("Enregistrer mon profil et évaluer mes chances", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

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
                st.rerun()

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
                st.success("CV analysé et profil enrichi !")
                st.json(resultat["donnees_extraites"])

if st.session_state.resultat_scoring:
    r = st.session_state.resultat_scoring

    st.markdown('<div class="boussole-card boussole-card-brass">', unsafe_allow_html=True)
    st.markdown("##### Tes chances estimées")
    st.markdown(cadran_boussole(r["tranche"]), unsafe_allow_html=True)
    st.markdown(
        f'<p style="text-align:center; font-family:Fraunces,serif; font-size:1.4rem; '
        f'font-weight:600; margin-top:0.5rem;">{r["tranche"]}</p>',
        unsafe_allow_html=True,
    )

    if not r["eligible"]:
        st.warning(
            "Au moins un critère éliminatoire n'est pas rempli : "
            + ", ".join(r["criteres_manquants_eliminatoires"])
        )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="boussole-card">', unsafe_allow_html=True)
    st.markdown("##### Détail par critère")
    for c in r["criteres"]:
        statut = "✅" if c["rempli"] else "❌"
        eliminatoire_tag = '<span class="tag-eliminatoire">Éliminatoire</span>' if c["eliminatoire"] else ""
        explication_html = f'<div class="critere-explication">{c["explication"]}</div>' if c["explication"] else ""
        st.markdown(html(f"""
        <div class="critere-ligne">
            <div class="critere-titre">{statut} {c['libelle']}{eliminatoire_tag}</div>
            <div class="critere-detail">Requis : {c['valeur_requise']} · Toi : {c['valeur_utilisateur'] or 'non renseigné'}</div>
            {explication_html}
        </div>
        """), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="boussole-card">', unsafe_allow_html=True)
    st.markdown("##### Ton plan d'action")
    plan = r["plan_coaching"]
    if plan.get("message_general"):
        st.markdown(f'<p style="color:var(--ink-muted); font-size:0.92rem;">{plan["message_general"]}</p>', unsafe_allow_html=True)
    for action in plan.get("actions", []):
        impact = action.get("impact", "Moyen")
        classe_impact = {"Fort": "impact-fort", "Moyen": "impact-moyen", "Faible": "impact-faible"}.get(impact, "impact-moyen")
        delai = action.get("delai_estime", "")
        delai_html = f' <span style="color:var(--ink-muted); font-size:0.82rem;">· {delai}</span>' if delai else ""
        st.markdown(html(f"""
        <div class="action-coaching">
            <span class="action-impact {classe_impact}">{impact}</span>
            <span>{action['action']}{delai_html}</span>
        </div>
        """), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    resultat_checklist, erreur = appeler_api(
        "GET", f"/checklist?pays={r['pays']}&type_demarche={r['type_demarche']}"
    )
    if erreur:
        st.error(erreur)
    else:
        st.markdown('<div class="boussole-card">', unsafe_allow_html=True)
        st.markdown("##### Documents à préparer")
        for doc in resultat_checklist["documents"]:
            tag_classe = "doc-obligatoire" if doc["obligatoire"] else "doc-optionnel"
            tag_texte = "Obligatoire" if doc["obligatoire"] else "Optionnel"
            sous_lignes = ""
            if doc["delai_obtention_estime"]:
                sous_lignes += f'<div class="doc-remarque">⏱ {doc["delai_obtention_estime"]}</div>'
            if doc["remarque"]:
                sous_lignes += f'<div class="doc-remarque">{doc["remarque"]}</div>'
            # Construit la ligne en une seule chaîne sans saut de ligne : une ligne vide
            # au milieu d'un bloc HTML injecté via st.markdown casse le parsing Markdown
            # et fait apparaître les balises suivantes en texte brut (bug déjà rencontré).
            html_doc = (
                f'<div class="doc-ligne"><div><div class="doc-nom">{doc["document"]}</div>'
                f'{sous_lignes}</div><span class="doc-tag {tag_classe}">{tag_texte}</span></div>'
            )
            st.markdown(html_doc, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div class="boussole-disclaimer">
    Ces informations sont indicatives et générées automatiquement. Vérifie toujours les exigences
    officielles à jour auprès des sources officielles (ambassade, Campus France, IRCC) avant toute démarche.
</div>
""", unsafe_allow_html=True)
