"""
Endpoints de gestion du profil utilisateur.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserProfile
from app.schemas.profile_schema import ProfileCreate, ProfileResponse

router = APIRouter(prefix="/profile", tags=["profil"])


@router.post("", response_model=ProfileResponse)
def creer_ou_mettre_a_jour_profil(data: ProfileCreate, db: Session = Depends(get_db)):
    """
    Crée un utilisateur + profil s'ils n'existent pas, sinon met à jour le profil existant.
    Identification par whatsapp_number OU email (au moins un requis).
    """
    if not data.whatsapp_number and not data.email:
        raise HTTPException(400, "whatsapp_number ou email requis pour identifier l'utilisateur.")

    user = None
    if data.whatsapp_number:
        user = db.query(User).filter(User.whatsapp_number == data.whatsapp_number).first()
    if not user and data.email:
        user = db.query(User).filter(User.email == data.email).first()

    if not user:
        user = User(whatsapp_number=data.whatsapp_number, email=data.email)
        db.add(user)
        db.flush()  # récupère user.id sans commit complet

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    champs_profil = data.model_dump(exclude={"whatsapp_number", "email"})

    if profile:
        for champ, valeur in champs_profil.items():
            if valeur is not None:
                setattr(profile, champ, valeur)
    else:
        profile = UserProfile(user_id=user.id, **champs_profil)
        db.add(profile)

    db.commit()
    db.refresh(profile)

    # whatsapp_number/email vivent sur User, pas UserProfile : on les rattache manuellement
    # à la réponse pour que l'utilisateur voie bien son numéro/email confirmé.
    reponse = ProfileResponse.model_validate(profile)
    reponse.whatsapp_number = user.whatsapp_number
    reponse.email = user.email
    return reponse


@router.get("/{user_id}", response_model=ProfileResponse)
def obtenir_profil(user_id: UUID, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(404, "Profil non trouvé.")

    user = db.query(User).filter(User.id == user_id).first()
    reponse = ProfileResponse.model_validate(profile)
    reponse.whatsapp_number = user.whatsapp_number
    reponse.email = user.email
    return reponse
