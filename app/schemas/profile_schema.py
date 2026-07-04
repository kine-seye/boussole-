"""
Schémas Pydantic : validation des données entrantes/sortantes de l'API.
"""
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ProfileCreate(BaseModel):
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None

    age: Optional[int] = Field(None, ge=15, le=80)
    nationalite: str = "Sénégal"

    niveau_diplome: Optional[str] = None
    domaine_etude: Optional[str] = None
    etablissement: Optional[str] = None
    annee_obtention: Optional[int] = None

    annees_experience: Optional[float] = Field(None, ge=0, le=50)
    secteur_activite: Optional[str] = None
    poste_actuel: Optional[str] = None

    langues: dict[str, str] = Field(default_factory=dict)
    capacite_financiere_fcfa: Optional[int] = Field(None, ge=0)

    pays_cible: Optional[str] = None
    type_demarche: Optional[str] = None

    @field_validator("niveau_diplome")
    @classmethod
    def valider_niveau_diplome(cls, v):
        valeurs_valides = {"Bac", "Bac+2", "Licence", "Master", "Doctorat", None}
        if v is not None and v not in valeurs_valides:
            raise ValueError(f"niveau_diplome doit être parmi {valeurs_valides}")
        return v


class ProfileResponse(ProfileCreate):
    id: UUID
    user_id: UUID
    donnees_source: str

    class Config:
        from_attributes = True


class ScoringRequest(BaseModel):
    user_id: UUID
    pays: str
    type_demarche: str


class CritereResultatResponse(BaseModel):
    libelle: str
    type_critere: str
    valeur_requise: str
    valeur_utilisateur: Optional[str]
    rempli: bool
    eliminatoire: bool
    explication: Optional[str]


class ScoringResponse(BaseModel):
    pays: str
    type_demarche: str
    tranche: str  # "Élevé" / "Moyen" / "Faible" -- pas de score numérique exposé à l'API publique
    eligible: bool
    criteres: list[CritereResultatResponse]
    criteres_manquants_eliminatoires: list[str]
    plan_coaching: dict


class ChecklistItemResponse(BaseModel):
    document: str
    obligatoire: bool
    delai_obtention_estime: Optional[str]
    remarque: Optional[str]


class ChecklistResponse(BaseModel):
    pays: str
    type_demarche: str
    documents: list[ChecklistItemResponse]
