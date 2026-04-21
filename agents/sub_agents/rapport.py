"""Agent Rapport — compilation et génération du compte-rendu journalier."""

from datetime import date
import anthropic
from agents.config import SUBAGENT_MODEL, RAPPORT_SYSTEM
from agents.utils import logger


def run(
    client: anthropic.Anthropic,
    planning: str,
    prospection: str,
    strategie: str,
    contexte_general: str,
) -> str:
    """
    Compile toutes les données et génère le compte-rendu journalier final.

    Args:
        client: Instance Anthropic partagée
        planning: Résultat de l'agent planification
        prospection: Résultat de l'agent prospection
        strategie: Résultat de l'agent stratégie
        contexte_general: Contexte général de la journée fourni par l'utilisateur

    Returns:
        Compte-rendu journalier complet en Markdown
    """
    logger.agent("RAPPORT", "Compilation du compte-rendu journalier...")

    today = date.today()
    # Noms de jours et mois en français
    jours_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    mois_fr = [
        "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre",
    ]
    date_fr = f"{jours_fr[today.weekday()]} {today.day} {mois_fr[today.month - 1]} {today.year}"

    user_message = f"""Compile toutes les données des agents et génère le compte-rendu journalier complet pour le {date_fr}.

═══════════════════════════════════════
CONTEXTE GÉNÉRAL DE LA JOURNÉE :
═══════════════════════════════════════
{contexte_general}

═══════════════════════════════════════
RÉSULTAT AGENT PLANIFICATION :
═══════════════════════════════════════
{planning}

═══════════════════════════════════════
RÉSULTAT AGENT PROSPECTION :
═══════════════════════════════════════
{prospection}

═══════════════════════════════════════
RÉSULTAT AGENT STRATÉGIE :
═══════════════════════════════════════
{strategie}

═══════════════════════════════════════

Génère le compte-rendu journalier complet selon la structure définie.
Intègre toutes les données de manière cohérente et priorisée.
Le rapport doit être directement utilisable sur le terrain."""

    response = client.messages.create(
        model=SUBAGENT_MODEL,
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": RAPPORT_SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    result = response.content[0].text
    logger.success("Agent Rapport terminé — compte-rendu généré")
    return result
