"""
Agent Travailleur — factory générique d'agents spécialisés.

Un agent travailleur est recruté dynamiquement par un chef d'équipe pour
accomplir une tâche précise et délimitée. Il ne peut pas recruter d'autres
agents (nœud feuille de la hiérarchie).
"""

import anthropic

from agents.config import WORKER_MODEL, WORKER_SYSTEM_TEMPLATE, BUSINESS
from agents.utils import logger


def run(
    client: anthropic.Anthropic,
    nom: str,
    specialite: str,
    tache: str,
    contexte: str,
) -> str:
    """
    Crée et exécute un agent travailleur spécialisé.

    Args:
        client:      Instance Anthropic partagée (pas de coût de ré-initialisation)
        nom:         Nom du rôle de l'agent  (ex: "Optimiseur d'Itinéraires")
        specialite:  Domaine d'expertise     (ex: "optimisation de trajets géographiques")
        tache:       Description précise de la mission à accomplir
        contexte:    Informations contextuelles nécessaires à l'agent

    Returns:
        Résultat formaté en texte Markdown
    """
    tag = f"TRAVAILLEUR › {nom[:28]}"
    logger.worker(tag, f"{tache[:90]}…")

    system = WORKER_SYSTEM_TEMPLATE.format(
        nom=nom,
        specialite=specialite,
        business_name=BUSINESS["name"],
        website=BUSINESS["website"],
    )

    response = client.messages.create(
        model=WORKER_MODEL,
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"TÂCHE ASSIGNÉE PAR TON CHEF D'ÉQUIPE :\n{tache}\n\n"
                    f"CONTEXTE :\n{contexte}"
                ),
            }
        ],
    )

    result = response.content[0].text
    logger.worker(tag, f"Mission accomplie — {len(result)} caractères")
    return result
