"""Agent Prospection — développement commercial et génération de leads."""

import anthropic
from agents.config import SUBAGENT_MODEL, PROSPECTION_SYSTEM
from agents.utils import logger


def run(client: anthropic.Anthropic, contexte: str, focus: str = "") -> str:
    """
    Identifie des opportunités commerciales et propose des actions de prospection.

    Args:
        client: Instance Anthropic partagée
        contexte: Contexte commercial actuel (pipeline, clients récents, actions précédentes)
        focus: Type de prospection à privilégier (optionnel)

    Returns:
        Analyse et plan de prospection en texte Markdown
    """
    logger.agent("PROSPECTION", "Analyse des opportunités commerciales...")

    focus_text = f"\n\nFOCUS DEMANDÉ : {focus}" if focus else ""

    user_message = f"""Analyse les opportunités commerciales et propose un plan de prospection pour aujourd'hui.

CONTEXTE COMMERCIAL ACTUEL :
{contexte}{focus_text}

Fournis des actions concrètes, des scripts de contact et des objectifs mesurables pour cette journée."""

    response = client.messages.create(
        model=SUBAGENT_MODEL,
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": PROSPECTION_SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    result = response.content[0].text
    logger.success("Agent Prospection terminé")
    return result
