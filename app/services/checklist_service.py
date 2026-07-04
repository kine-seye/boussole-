"""
Service checklist : récupère les documents requis pour un (pays, type_demarche),
triés dans un ordre logique d'obtention.
"""
from sqlalchemy.orm import Session

from app.models.criteria import DocumentChecklist


def obtenir_checklist(db: Session, pays: str, type_demarche: str) -> list[dict]:
    documents = (
        db.query(DocumentChecklist)
        .filter(DocumentChecklist.pays == pays, DocumentChecklist.type_demarche == type_demarche)
        .order_by(DocumentChecklist.ordre_affichage)
        .all()
    )

    if not documents:
        raise ValueError(f"Aucune checklist trouvée pour {pays} / {type_demarche}")

    return [
        {
            "document": d.document,
            "obligatoire": d.obligatoire,
            "delai_obtention_estime": d.delai_obtention_estime,
            "remarque": d.remarque,
        }
        for d in documents
    ]
