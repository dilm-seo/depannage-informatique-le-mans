"""Agent Planification — organisation et planning journalier optimisé."""

import anthropic
from agents.config import SUBAGENT_MODEL, PLANIFICATION_SYSTEM
from agents.utils import logger


def run(client: anthropic.Anthropic, contexte: str, priorites: list[str] | None = None) -> str:
    """
    Génère un planning journalier optimisé basé sur le contexte fourni.

    Args:
        client: Instance Anthropic partagée
        contexte: Description de la situation du jour (tâches, rdv, urgences)
        priorites: Liste optionnelle de priorités ou tâches importantes

    Returns:
        Planning structuré en texte Markdown
    """
    logger.agent("PLANIFICATION", "Génération du planning journalier...")

    priorites_text = ""
    if priorites:
        priorites_text = "\n\nPRIORITÉS IDENTIFIÉES :\n" + "\n".join(f"  - {p}" for p in priorites)

    user_message = f"""Génère le planning optimisé pour cette journée.

CONTEXTE DU JOUR :
{contexte}{priorites_text}

Crée un planning détaillé, optimisé géographiquement et centré sur la rentabilité."""

    response = client.messages.create(
        model=SUBAGENT_MODEL,
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": PLANIFICATION_SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    result = response.content[0].text
    logger.success("Agent Planification terminé")
    return result
