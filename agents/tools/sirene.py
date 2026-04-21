"""
Outil SIRENE — nouvelles entreprises immatriculées dans la Sarthe.

Utilise l'API officielle gratuite recherche-entreprises.api.gouv.fr
Aucun compte ni clé API requise.

Idéal pour prospecter les entreprises qui viennent d'ouvrir :
  → Pas encore de prestataire informatique
  → Besoin urgent de setup PC, réseau, logiciels
  → Réceptives à un premier contact professionnel
"""

from __future__ import annotations

import json
import urllib.request
import urllib.parse
from datetime import date, timedelta

_API_URL = "https://recherche-entreprises.api.gouv.fr/search"

# Codes NAF ciblés — secteurs à forte dépendance informatique
SECTEURS_CIBLES = {
    "86": "Santé (médecins, dentistes, kinés)",
    "69": "Juridique et comptabilité (avocats, notaires, experts-comptables)",
    "41": "Construction / BTP",
    "43": "Travaux de construction spécialisés (plombiers, électriciens)",
    "56": "Restauration",
    "47": "Commerce de détail",
    "68": "Immobilier (agences)",
    "85": "Enseignement",
    "96": "Services personnels (coiffeurs, esthétique)",
    "55": "Hébergement",
}


def chercher_nouvelles_entreprises(
    departement: str = "72",
    jours: int = 30,
    secteur_naf: str = "",
    max_resultats: int = 10,
) -> str:
    """
    Cherche les entreprises récemment créées dans la Sarthe.

    Args:
        departement:   Code département (72 pour Sarthe)
        jours:         Fenêtre de création (derniers N jours)
        secteur_naf:   Préfixe NAF (ex: "86" pour santé, "69" pour juridique)
        max_resultats: Nombre max de résultats

    Returns:
        Liste formatée des nouvelles entreprises avec coords et secteur
    """
    date_min = (date.today() - timedelta(days=jours)).isoformat()

    params: dict[str, str] = {
        "departement": departement,
        "date_creation_min": date_min,
        "per_page": str(min(max_resultats * 3, 25)),  # on surcharge pour filtrer
        "page": "1",
        "categorie_entreprise": "PME",   # exclut les grandes entreprises nationales
    }
    if secteur_naf:
        params["activite_principale"] = secteur_naf

    url = f"{_API_URL}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Fix72-Agents/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return f"[ERREUR] SIRENE API : {e}"

    entreprises = data.get("results", [])
    if not entreprises:
        return f"Aucune nouvelle PME/TPE trouvée en Sarthe (72) depuis {jours} jours."

    # Filtrer : garder seulement les entreprises créées après date_min ET avec siège en Sarthe
    locales = []
    for e in entreprises:
        siege = e.get("siege", {})
        cp = siege.get("code_postal", "")
        date_creation = e.get("date_creation", "")
        # Vérifier siège en Sarthe et création récente
        if cp.startswith("72") and date_creation >= date_min:
            locales.append(e)
        if len(locales) >= max_resultats:
            break

    if not locales:
        return f"Aucune nouvelle TPE/PME locale trouvée en Sarthe (72) depuis {jours} jours."

    lignes = [f"Nouvelles TPE/PME Sarthe (72) créées depuis {jours} jours :\n"]
    for e in locales:
        nom = e.get("nom_complet") or e.get("nom_raison_sociale") or "Nom inconnu"
        naf = e.get("activite_principale", "")
        libelle_naf = e.get("libelle_activite_principale", naf)
        siege = e.get("siege", {})
        ville = siege.get("libelle_commune", "")
        cp = siege.get("code_postal", "")
        adresse = siege.get("adresse", "")
        date_creation = e.get("date_creation", "")
        dirigeant = ""
        dirigeants = e.get("dirigeants", [])
        if dirigeants:
            d = dirigeants[0]
            dirigeant = f"{d.get('prenoms', '')} {d.get('nom', '')}".strip()

        lignes.append(f"• **{nom}**")
        lignes.append(f"  Activité : {libelle_naf} (NAF {naf})")
        lignes.append(f"  Créée le : {date_creation}")
        lignes.append(f"  Adresse : {adresse}, {cp} {ville}")
        if dirigeant:
            lignes.append(f"  Dirigeant : {dirigeant}")
        lignes.append("")

    return "\n".join(lignes)


def chercher_tous_secteurs(departement: str = "72", jours: int = 14) -> str:
    """Lance une recherche sur tous les secteurs cibles en une fois."""
    resultats = []
    for naf, label in list(SECTEURS_CIBLES.items())[:5]:
        r = chercher_nouvelles_entreprises(departement=departement, jours=jours, secteur_naf=naf, max_resultats=5)
        if "ERREUR" not in r and "Aucune" not in r:
            resultats.append(f"=== {label} ===\n{r}")
    return "\n\n".join(resultats) if resultats else "Aucun résultat trouvé."


# ─── Outil Anthropic ──────────────────────────────────────────────────────────

OUTIL_SIRENE: dict = {
    "name": "chercher_nouvelles_entreprises_sirene",
    "description": (
        "Recherche les entreprises récemment créées dans la Sarthe via l'API SIRENE officielle. "
        "Ces entreprises viennent d'ouvrir et n'ont pas encore de prestataire informatique — "
        "ce sont les meilleurs prospects car ils ont un besoin immédiat. "
        "Utilise cet outil en priorité avant la recherche web classique."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "jours": {
                "type": "integer",
                "description": "Fenêtre de création en jours (défaut: 30, max: 90)",
                "default": 30,
            },
            "secteur_naf": {
                "type": "string",
                "description": (
                    "Préfixe du code NAF pour filtrer par secteur. "
                    "Exemples : '86' (santé), '69' (juridique/compta), '43' (artisans BTP), "
                    "'56' (restauration), '68' (immobilier). Laisser vide pour tous secteurs."
                ),
                "default": "",
            },
            "max_resultats": {
                "type": "integer",
                "description": "Nombre de résultats à retourner (défaut: 10, max: 25)",
                "default": 10,
            },
        },
    },
}
