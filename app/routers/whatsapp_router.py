"""
Webhook Meta WhatsApp Cloud API.

Deux routes standard exigées par Meta :
- GET  : vérification du webhook lors de la configuration (hub.challenge)
- POST : réception des messages entrants
"""
from fastapi import APIRouter, Request, Response, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.services.conversation_service import traiter_message_entrant
from app.services.whatsapp_service import envoyer_message_whatsapp

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
settings = get_settings()


@router.get("/webhook")
def verifier_webhook(request: Request):
    """
    Meta appelle cette route une seule fois, lors de la configuration du webhook
    dans le tableau de bord développeur, pour vérifier que le serveur nous appartient.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(content="Verification failed", status_code=403)


@router.post("/webhook")
async def recevoir_message(request: Request, db: Session = Depends(get_db)):
    """
    Reçoit les événements WhatsApp entrants. On ne traite que les vrais messages
    texte d'un utilisateur (Meta envoie aussi des accusés de lecture/statuts qu'on ignore).
    """
    payload = await request.json()

    try:
        entree = payload["entry"][0]["changes"][0]["value"]
        messages = entree.get("messages")
        if not messages:
            # Statut de livraison/lecture, pas un vrai message -> rien à faire
            return {"statut": "ignore"}

        message = messages[0]
        numero_expediteur = message["from"]
        type_message = message.get("type")

        if type_message != "text":
            envoyer_message_whatsapp(
                numero_expediteur,
                "Je ne peux traiter que des messages texte pour le moment 🙏",
            )
            return {"statut": "type_non_supporte"}

        texte = message["text"]["body"]

        reponse_texte = traiter_message_entrant(db, numero_expediteur, texte)
        envoyer_message_whatsapp(numero_expediteur, reponse_texte)

        return {"statut": "traite"}

    except (KeyError, IndexError) as e:
        # Format de payload inattendu (ex: notification autre que message) -> on ignore proprement
        print(f"⚠️ Payload webhook non reconnu : {e}")
        return {"statut": "payload_non_reconnu"}
