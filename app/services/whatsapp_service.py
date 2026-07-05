"""
Envoi de messages sortants via l'API Meta WhatsApp Cloud.
Isolé dans son propre service pour pouvoir facilement le mocker en tests
sans dépendre d'un vrai appel réseau vers Meta.
"""
import requests

from app.config import get_settings

settings = get_settings()


def envoyer_message_whatsapp(numero_destinataire: str, texte: str) -> bool:
    """
    Envoie un message texte WhatsApp. Retourne True si Meta a accepté l'envoi,
    False sinon (log l'erreur mais ne lève jamais d'exception : un échec d'envoi
    ne doit jamais faire planter le traitement du webhook).
    """
    if not settings.WHATSAPP_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        print("⚠️ WHATSAPP_TOKEN ou WHATSAPP_PHONE_NUMBER_ID non configuré — message non envoyé.")
        return False

    url = f"https://graph.facebook.com/v21.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destinataire,
        "type": "text",
        "text": {"body": texte},
    }

    try:
        reponse = requests.post(url, headers=headers, json=payload, timeout=15)
        reponse.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Échec envoi WhatsApp à {numero_destinataire} : {e}")
        return False
