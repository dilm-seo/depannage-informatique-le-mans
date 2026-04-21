"""
Outils de recherche web pour les agents travailleurs de prospection.
Utilise DDGS (DuckDuckGo Search, sans clé API requise).
"""

from __future__ import annotations
import time

try:
    from ddgs import DDGS
    _DDG_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        _DDG_AVAILABLE = True
    except ImportError:
        _DDG_AVAILABLE = False


def _ddg_text(query: str, max_results: int) -> list[dict]:
    """Appel DDG avec retry en cas de rate limit."""
    for attempt in range(3):
        try:
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=max_results))
        except Exception as e:
            if "ratelimit" in str(e).lower() or "429" in str(e):
                time.sleep(2 ** attempt)
            else:
                raise
    return []


def rechercher_web(query: str, max_results: int = 8) -> str:
    """Recherche sur le web via DuckDuckGo et retourne les résultats formatés."""
    if not _DDG_AVAILABLE:
        return (
            "[ERREUR] Module ddgs non installé.\n"
            "Lancez : pip install ddgs"
        )

    try:
        results = _ddg_text(query, min(max_results, 15))
    except Exception as e:
        return f"[ERREUR] Recherche web échouée pour '{query}' : {e}"

    if not results:
        return f"Aucun résultat trouvé pour : {query}"

    lines = [f"Résultats de recherche pour : **{query}**\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. **{r.get('title', 'Sans titre')}**")
        lines.append(f"   URL : {r.get('href', '')}")
        body = r.get("body", "").strip()
        if body:
            lines.append(f"   {body[:300]}")
        lines.append("")
    return "\n".join(lines)


def rechercher_entreprises_local(secteur: str, ville: str = "Le Mans") -> str:
    """
    Recherche des entreprises locales dans un secteur d'activité pour prospection.
    Effectue plusieurs requêtes ciblées (Pages Jaunes, annuaires locaux).
    """
    if not _DDG_AVAILABLE:
        return "[ERREUR] Module ddgs non installé."

    queries = [
        f"{secteur} {ville} Sarthe téléphone adresse",
        f"entreprise {secteur} {ville} 72 contact",
    ]

    all_results: list[dict] = []
    try:
        for query in queries:
            results = _ddg_text(query, 6)
            all_results.extend(results)
            time.sleep(0.5)  # éviter le rate limit entre requêtes
    except Exception as e:
        return f"[ERREUR] Recherche locale échouée pour '{secteur}' : {e}"

    if not all_results:
        return f"Aucune entreprise trouvée pour le secteur '{secteur}' à {ville}."

    # Dédupliquer par URL
    seen: set[str] = set()
    unique: list[dict] = []
    for r in all_results:
        url = r.get("href", "")
        if url not in seen:
            seen.add(url)
            unique.append(r)

    lines = [f"Entreprises '{secteur}' à {ville} (Sarthe 72) :\n"]
    for i, r in enumerate(unique[:12], 1):
        lines.append(f"{i}. **{r.get('title', 'Sans titre')}**")
        lines.append(f"   {r.get('href', '')}")
        body = r.get("body", "").strip()
        if body:
            lines.append(f"   {body[:250]}")
        lines.append("")
    return "\n".join(lines)


# ─── Définitions des outils (format Anthropic tool use) ──────────────────────

OUTIL_RECHERCHE_WEB: dict = {
    "name": "rechercher_web",
    "description": (
        "Effectue une recherche sur le web via DuckDuckGo. "
        "Utilise pour trouver des informations sur des entreprises locales, "
        "des contacts, des actualités ou des données de marché. "
        "Retourne titre, URL et extrait pour chaque résultat."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "La requête de recherche. Sois précis et utilise des termes locaux. "
                    "Exemples : 'plombier Le Mans 72 contact téléphone', "
                    "'cabinet comptable Sarthe PME informatique maintenance'."
                ),
            },
            "max_results": {
                "type": "integer",
                "description": "Nombre de résultats à retourner (défaut: 8, max: 15)",
                "default": 8,
            },
        },
        "required": ["query"],
    },
}

OUTIL_RECHERCHE_ENTREPRISES: dict = {
    "name": "rechercher_entreprises_local",
    "description": (
        "Recherche des entreprises locales dans un secteur d'activité donné "
        "pour identifier des prospects réels à contacter. "
        "Interroge les annuaires locaux (Pages Jaunes, Google, etc.) via DuckDuckGo. "
        "Retourne noms, coordonnées et descriptions des entreprises trouvées."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "secteur": {
                "type": "string",
                "description": (
                    "Secteur d'activité des prospects à rechercher. "
                    "Exemples : 'plombier', 'cabinet comptable', 'restaurant', "
                    "'pharmacie', 'agence immobilière', 'cabinet médical', "
                    "'électricien', 'boulangerie', 'avocat', 'notaire'."
                ),
            },
            "ville": {
                "type": "string",
                "description": "Ville ou zone de recherche (défaut: 'Le Mans')",
                "default": "Le Mans",
            },
        },
        "required": ["secteur"],
    },
}

# Liste complète des outils pour les workers de prospection (web + Telegram + Email)
from agents.tools.telegram import OUTIL_TELEGRAM
from agents.tools.email import OUTIL_EMAIL
OUTILS_PROSPECTION: list[dict] = [OUTIL_RECHERCHE_WEB, OUTIL_RECHERCHE_ENTREPRISES, OUTIL_TELEGRAM, OUTIL_EMAIL]
