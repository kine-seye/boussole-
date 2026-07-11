"""
Point d'entrée de l'application Boussole.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import profile_router, cv_router, scoring_router, checklist_router, whatsapp_router, chat_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="Agent d'évaluation des chances d'immigration/bourses pour candidats sénégalais.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # à restreindre en production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile_router.router)
app.include_router(cv_router.router)
app.include_router(scoring_router.router)
app.include_router(checklist_router.router)
app.include_router(whatsapp_router.router)
app.include_router(chat_router.router)


@app.get("/")
def racine():
    return {
        "app": settings.APP_NAME,
        "statut": "actif",
        "pays_disponibles": ["Canada", "France"],
        "demarches_disponibles": ["visa_etudiant", "bourse"],
    }


@app.get("/health")
def health_check():
    return {"statut": "ok"}
