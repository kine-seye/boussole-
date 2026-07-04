"""
Configuration centralisée de l'application.
Toutes les variables sensibles viennent des variables d'environnement.
"""
import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Base de données PostgreSQL (dès le départ, contrairement à Sefa qui a commencé en SQLite)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://boussole_user:changeme@localhost:5432/boussole_db",
    )

    # LLM - Groq (Llama 3.3 70B), même stack que Sefa Bien-être
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # WhatsApp Cloud API (Meta) - réutilise la config Sefa
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "boussole_verify")

    # Upload CV
    MAX_CV_SIZE_MB: int = 5
    ALLOWED_CV_EXTENSIONS: tuple = (".pdf",)

    # App
    APP_NAME: str = "Boussole"
    ENV: str = os.getenv("ENV", "development")


@lru_cache
def get_settings() -> Settings:
    return Settings()
