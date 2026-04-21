"""Agent Stratégie — analyse stratégique et recommandations business."""

import anthropic
from agents.config import SUBAGENT_MODEL, STRATEGIE_SYSTEM
from agents.utils import logger


def run(
    client: anthropic.Anthropic,
    contexte: str,
    questions: list[str] | None = None,
) -> str:
    """
    Produit une analyse stratégique et des recommandations business.

    Args:
        client: Instance Anthropic partagée
        contexte: Situation actuelle de l'entreprise et points à analyser
        questions: Questions stratégiques spécifiques à adresser (optionnel)

    Returns:
        Analyse stratégique et recommandations en texte Markdown
    """
    logger.agent("STRATÉGIE", "Analyse stratégique en cours...")

    questions_text = ""
    if questions:
        questions_text = "\n\nQUESTIONS STRATÉGIQUES À ADRESSER :\n" + "\n".join(
            f"  {i+1}. {q}" for i, q in enumerate(questions)
        )

    user_message = f"""Réalise l'analyse stratégique pour cette journée et fournis tes recommandations.

CONTEXTE DE L'ENTREPRISE :
{contexte}{questions_text}

Fournis des insights actionnables, une analyse SWOT synthétique et des recommandations prioritaires à court et moyen terme."""

    response = client.messages.create(
        model=SUBAGENT_MODEL,
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": STRATEGIE_SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    result = response.content[0].text
    logger.success("Agent Stratégie terminé")
    return result
