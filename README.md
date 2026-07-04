# Boussole — Phase 1 (MVP)

Agent d'évaluation des chances d'immigration/bourses (Canada, France) pour candidats
sénégalais : profil + CV → score par critère → coaching personnalisé → checklist documents.

✅ **Ce pipeline a été testé de bout en bout** (migration → seed → API → requêtes réelles)
sur une vraie base PostgreSQL avant livraison. Les instructions ci-dessous sont donc
directement opérationnelles, pas théoriques.

## Prérequis

- Python 3.11+
- PostgreSQL 14+ (installé et démarré)
- Un compte [Groq](https://console.groq.com) pour la clé API (gratuit, utilisé pour le coach IA et l'extraction CV)

## 1. Installation

```bash
cd boussole
python3 -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configuration

```bash
cp .env.example .env
```

Édite `.env` et renseigne au minimum :
```
DATABASE_URL=postgresql://boussole_user:TON_MOT_DE_PASSE@localhost:5432/boussole_db
GROQ_API_KEY=ta_clé_groq
```

**Sans GROQ_API_KEY** : l'app fonctionne quand même — le coach retombe automatiquement
sur un plan déterministe (moins bien formulé mais fonctionnel), et l'upload CV renverra
une erreur claire tant que la clé n'est pas configurée.

## 3. Créer la base PostgreSQL

```bash
sudo -u postgres psql -c "CREATE USER boussole_user WITH PASSWORD 'TON_MOT_DE_PASSE';"
sudo -u postgres psql -c "CREATE DATABASE boussole_db OWNER boussole_user;"
```

## 4. Appliquer les migrations (crée les 5 tables)

```bash
alembic upgrade head
```

Vérifie que ça a marché :
```bash
sudo -u postgres psql -d boussole_db -c '\dt'
# Doit lister : users, profiles, countries_criteria, documents_checklist, scoring_history
```

## 5. Peupler les critères Canada/France

```bash
PYTHONPATH=. python3 seeds/seed_criteria.py
```

⚠️ **Important** : le script doit être lancé avec `PYTHONPATH=.` sinon il ne trouve pas
le module `app`. C'est le bug le plus probable si tu obtiens `ModuleNotFoundError: No module named 'app'`.

Ça peuple : Canada (visa étudiant + bourse) et France (visa étudiant + bourse Eiffel),
critères d'éligibilité + checklists documentaires.

## 6. Lancer le serveur

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Ouvre **http://localhost:8000/docs** — tu as l'interface Swagger interactive pour tester
chaque endpoint directement dans le navigateur, sans écrire de code.

## 7. Test rapide en 3 appels

**a) Créer un profil**
```bash
curl -X POST http://localhost:8000/profile \
  -H "Content-Type: application/json" \
  -d '{
    "whatsapp_number": "221771234567",
    "age": 24,
    "niveau_diplome": "Master",
    "domaine_etude": "Informatique",
    "annees_experience": 1.5,
    "langues": {"francais": "C2", "anglais": "B2"},
    "capacite_financiere_fcfa": 15000000,
    "pays_cible": "Canada",
    "type_demarche": "bourse"
  }'
```
→ note le `user_id` retourné.

**b) Calculer le score**
```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{"user_id": "TON_USER_ID", "pays": "Canada", "type_demarche": "bourse"}'
```
→ retourne la tranche (Élevé/Moyen/Faible), le détail ✅❌ par critère, et le plan de coaching.

**c) Récupérer la checklist documents**
```bash
curl "http://localhost:8000/checklist?pays=France&type_demarche=visa_etudiant"
```

## Bugs déjà corrigés pendant les tests (pour info)

1. **Seed nécessite `PYTHONPATH=.`** — sans ça, `ModuleNotFoundError`. Documenté ci-dessus.
2. **whatsapp_number/email absents de la réponse `/profile`** — corrigé : ces champs
   vivent sur la table `users`, pas `profiles`, ils sont maintenant rattachés manuellement
   à la réponse.

## Ce qui n'est PAS encore fait (rappel du scope Phase 1)

- ❌ Pas de bot WhatsApp connecté (prévu semaine 6 de la roadmap)
- ❌ Pas de dashboard web Streamlit (prévu semaine 7)
- ❌ Pas de génération de CV/lettre de motivation (Phase 2)
- ❌ Scope volontairement limité à Canada + France, visa étudiant + bourse

## Prochaine étape suggérée

Une fois ce pipeline validé de ton côté, on attaque soit :
- l'intégration WhatsApp (réutilise ton infra Sefa existante), soit
- le dashboard Streamlit (affichage visuel du score et du plan de coaching)

Dis-moi lequel tu préfères démarrer en premier.
