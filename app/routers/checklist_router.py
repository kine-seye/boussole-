"""
Endpoint checklist documents.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.checklist_service import obtenir_checklist
from app.schemas.profile_schema import ChecklistResponse

router = APIRouter(prefix="/checklist", tags=["checklist"])


@router.get("", response_model=ChecklistResponse)
def get_checklist(pays: str, type_demarche: str, db: Session = Depends(get_db)):
    try:
        documents = obtenir_checklist(db, pays, type_demarche)
    except ValueError as e:
        raise HTTPException(404, str(e))

    return ChecklistResponse(pays=pays, type_demarche=type_demarche, documents=documents)
