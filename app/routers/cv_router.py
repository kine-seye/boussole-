"""
Endpoint d'upload et extraction de CV.
"""
import os
import tempfile
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User, UserProfile
from app.services.cv_service import (
    extraire_texte_pdf, extraire_donnees_structurees, fusionner_avec_profil_existant,
)

router = APIRouter(prefix="/cv", tags=["cv"])
settings = get_settings()


@router.post("/upload")
async def uploader_cv(user_id: UUID, fichier: UploadFile = File(...), db: Session = Depends(get_db)):
    # Validations de base
    if not fichier.filename.lower().endswith(settings.ALLOWED_CV_EXTENSIONS):
        raise HTTPException(400, f"Format non supporté. Formats acceptés : {settings.ALLOWED_CV_EXTENSIONS}")

    contenu = await fichier.read()
    taille_mb = len(contenu) / (1024 * 1024)
    if taille_mb > settings.MAX_CV_SIZE_MB:
        raise HTTPException(400, f"Fichier trop volumineux ({taille_mb:.1f} Mo, max {settings.MAX_CV_SIZE_MB} Mo).")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé. Crée d'abord un profil via /profile.")

    # Sauvegarde temporaire pour extraction
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(contenu)
        chemin_tmp = tmp.name

    try:
        texte_cv = extraire_texte_pdf(chemin_tmp)
        donnees_cv = extraire_donnees_structurees(texte_cv)

        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        profil_existant_dict = (
            {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
            if profile else {}
        )

        donnees_fusionnees = fusionner_avec_profil_existant(donnees_cv, profil_existant_dict)

        if profile:
            for champ, valeur in donnees_fusionnees.items():
                if hasattr(profile, champ) and champ not in ("id", "user_id"):
                    setattr(profile, champ, valeur)
        else:
            donnees_fusionnees.pop("id", None)
            donnees_fusionnees.pop("user_id", None)
            profile = UserProfile(user_id=user_id, **donnees_fusionnees)
            db.add(profile)

        profile.cv_brut_json = donnees_cv
        db.commit()
        db.refresh(profile)

        return {
            "message": "CV analysé et profil mis à jour avec succès.",
            "donnees_extraites": donnees_cv,
            "confiance_extraction": donnees_cv.get("confiance_extraction", "moyenne"),
        }

    except ValueError as e:
        raise HTTPException(422, str(e))
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    except Exception as e:
        # Filet de sécurité : toute exception non anticipée (ex: PDF corrompu,
        # bug pdfplumber sur un format particulier) devient une erreur lisible
        # au lieu d'un 500 muet sans explication pour l'utilisateur.
        raise HTTPException(500, f"Erreur inattendue pendant le traitement du CV : {e}")
    finally:
        os.unlink(chemin_tmp)  # nettoyage systématique du fichier temporaire
