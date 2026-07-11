# 🧭 Boussole

Agent d'évaluation des chances d'immigration et de bourses d'études (Canada, France)
pour candidats sénégalais. Profil (ou CV) → score par critère → plan de coaching
personnalisé (IA) → checklist documentaire — accessible en ligne via web ou WhatsApp.

## 🔗 Liens

- **Dashboard en ligne** : [tyz3i2ne3seihunkyyrswm.streamlit.app](https://tyz3i2ne3seihunkyyrswm.streamlit.app)
- **API backend** : [boussole-api-fusi.onrender.com/docs](https://boussole-api-fusi.onrender.com/docs)

> ⚠️ Le backend tourne sur un plan gratuit Render : il se met en veille après inactivité,
> la première requête peut prendre jusqu'à 50 secondes à répondre.

## Fonctionnalités

- **Profil déclaratif + extraction CV** (PDF) via LLM, fusionnés intelligemment
- **Scoring par critère** (✅/❌) pondéré, avec détection des critères éliminatoires
- **Coach IA** (Groq / Llama 3.3 70B) : plan d'action priorisé par impact, pas juste un score brut
- **Checklist documentaire** par pays et type de démarche
- **Dashboard web** avec identité visuelle propre (cadran de boussole SVG pour visualiser
  les chances en tranche Faible/Moyen/Élevé — jamais un faux score numérique précis)
- **Intégration WhatsApp** (Meta Cloud API) : conversation guidée étape par étape — *en pause,
  en attente d'un numéro dédié*

## Stack technique

| Composant | Techno |
|---|---|
| Backend API | FastAPI + SQLAlchemy + Alembic |
| Base de données | PostgreSQL (Render) |
| LLM | Groq (Llama 3.3 70B) |
| Dashboard | Streamlit (Streamlit Community Cloud) |
| Messagerie | Meta WhatsApp Cloud API |
| Extraction CV | pdfplumber + LLM |
| Déploiement | Render (API + DB) + Streamlit Cloud (dashboard) |

## Scope actuel

Canada et France, visa étudiant et bourse d'études. Conçu pour être étendu facilement
(nouveau pays/démarche = nouvelles lignes dans `countries_criteria` et `documents_checklist`,
aucun changement de code).

---

## Installation locale (développement)

### Prérequis
- Python 3.11+
- PostgreSQL 14+
- Un compte [Groq](https://console.groq.com) (clé API gratuite)

### 1. Installation
```bash
cd boussole
python3 -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration
```bash
cp .env.example .env
```
Renseigne au minimum `DATABASE_URL` et `GROQ_API_KEY` dans `.env`.

### 3. Base de données
```bash
sudo -u postgres psql -c "CREATE USER boussole_user WITH PASSWORD 'TON_MOT_DE_PASSE';"
sudo -u postgres psql -c "CREATE DATABASE boussole_db OWNER boussole_user;"
alembic upgrade head
PYTHONPATH=. python3 seeds/seed_criteria.py
```

### 4. Lancer le backend
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
→ Doc interactive sur `http://localhost:8000/docs`

### 5. Lancer le dashboard (terminal séparé)
```bash
streamlit run dashboard/app.py
```
→ `http://localhost:8501`

## Structure du projet

```
boussole/
├── app/
│   ├── models/          # User, UserProfile, CountryCriteria, DocumentChecklist, ConversationState
│   ├── routers/          # profile, cv, scoring, checklist, whatsapp
│   ├── services/          # scoring, coach (LLM), cv extraction, whatsapp, conversation
│   └── main.py
├── dashboard/
│   └── app.py            # Interface Streamlit
├── alembic/               # Migrations
├── seeds/                 # Peuplement des critères pays/démarches
└── requirements.txt
```

## Points de conception notables

- **Aucun score numérique précis affiché à l'utilisateur** — seulement une tranche
  qualitative (Faible/Moyen/Élevé), pour éviter une fausse impression de certitude
  scientifique sur un sujet à fort enjeu (immigration).
- **Le CV enrichit le profil sans jamais écraser une déclaration manuelle** de l'utilisateur.
- **Coach avec fallback déterministe** : si l'appel LLM échoue, un plan d'action basique
  (trié par poids des critères manquants) est généré à la place — jamais de plantage silencieux.

## Roadmap

- [x] Phase 1 — MVP : scoring, coach, checklist, CV, dashboard, déploiement
- [ ] Connexion WhatsApp (bloqué : en attente d'un numéro dédié)
- [ ] Génération de CV / lettre de motivation adaptés (Phase 2)
- [ ] Suivi de candidatures, alertes personnalisées (Phase 3)
- [ ] Extension à d'autres pays/démarches

## Auteure

[Kiné Seye](https://www.linkedin.com/in/kine-seye-b513b13ba) — Data Scientist & AI Developer,
Dakar, Sénégal.
