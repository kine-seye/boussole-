"""
Recherche web en direct, utilisée quand ni la base de données (critères/checklist/FAQ)
ni l'historique ne suffisent à répondre à une question. Utilise Tavily (API pensée pour
les agents LLM, résultats concis avec sources), pas un moteur de recherche générique.

Dégradation gracieuse : si la clé n'est pas configurée, la fonction retourne simplement
qu'aucune recherche n'est disponible, sans jamais planter le chatbot.
"""
import requests

from app.config import get_settings

settings = get_settings()

TAVILY_URL = "https://api.tavily.com/search"


def rechercher_web(requete: str, nb_resultats: int = 3) -> list[dict]:
    """
    Effectue une recherche web et retourne une liste de résultats structurés
    (titre, extrait, url). Retourne une liste vide si la clé n'est pas configurée
    ou si la recherche échoue — jamais d'exception remontée à l'appelant.
    """
    if not settings.TAVILY_API_KEY:
        return []

    try:
        reponse = requests.post(
            TAVILY_URL,
            json={
                "api_key": settings.TAVILY_API_KEY,
                "query": requete,
                "search_depth": "basic",
                "max_results": nb_resultats,
                "include_answer": False,
            },
            timeout=10,
        )
        reponse.raise_for_status()
        data = reponse.json()

        return [
            {
                "titre": r.get("title", ""),
                "extrait": r.get("content", "")[:500],
                "url": r.get("url", ""),
            }
            for r in data.get("results", [])
        ]
    except Exception as e:
        print(f"⚠️ Échec recherche web pour '{requete}' : {e}")
        return []
