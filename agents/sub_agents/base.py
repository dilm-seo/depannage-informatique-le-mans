"""
ChefEquipe — classe de base pour tous les agents chefs d'équipe.

Un chef d'équipe :
  • Reçoit une directive précise du Superviseur
  • Peut recruter des agents travailleurs spécialisés via `recruter_agent_specialise`
  • Exécute sa propre boucle agentique (tool use)
  • Rend compte au Superviseur avec un rapport structuré et un niveau de confiance
"""

from __future__ import annotations

from dataclasses import dataclass, field

import anthropic

from agents.config import CHEF_MODEL
from agents.agent_travailleur import run as run_worker
from agents.utils import logger

# ─── Outil disponible pour tous les chefs d'équipe ───────────────────────────

OUTIL_RECRUTEMENT: dict = {
    "name": "recruter_agent_specialise",
    "description": (
        "Recrute un agent travailleur spécialisé pour accomplir une sous-tâche précise. "
        "Utilise cet outil uniquement quand la tâche requiert une expertise spécifique "
        "que tu ne peux pas fournir seul efficacement. "
        "L'agent retourne son résultat directement dans cette conversation."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "nom_agent": {
                "type": "string",
                "description": (
                    "Nom du rôle de l'agent recruté "
                    "(ex: 'Optimiseur d\\'Itinéraires', 'Rédacteur de Messages')"
                ),
            },
            "specialite": {
                "type": "string",
                "description": "Domaine d'expertise précis de l'agent",
            },
            "tache": {
                "type": "string",
                "description": "Description précise et complète de la tâche à accomplir",
            },
            "contexte": {
                "type": "string",
                "description": "Toutes les informations contextuelles nécessaires à l'agent",
            },
        },
        "required": ["nom_agent", "specialite", "tache", "contexte"],
    },
}


# ─── Résultat d'un chef d'équipe ──────────────────────────────────────────────

@dataclass
class RapportEquipe:
    rapport: str
    agents_recrutes: list[str] = field(default_factory=list)
    confidence: int = 80        # pourcentage 0-100

    def to_supervisor_text(self) -> str:
        """Formate le rapport pour la lecture du Superviseur."""
        recrutes = ", ".join(self.agents_recrutes) if self.agents_recrutes else "aucun"
        return (
            f"**Agents recrutés :** {recrutes}\n"
            f"**Niveau de confiance :** {self.confidence} %\n\n"
            f"{self.rapport}"
        )


# ─── Classe de base ───────────────────────────────────────────────────────────

class ChefEquipe:
    """Base pour planification, prospection et stratégie."""

    MAX_ITERATIONS = 8
    worker_tools: list[dict] = []  # Outils passés aux workers recrutés (override dans les sous-classes)

    def __init__(self, nom: str, system_prompt: str) -> None:
        self.nom = nom
        self.system_prompt = system_prompt

    def run(
        self,
        client: anthropic.Anthropic,
        directive: str,
        contexte: str,
        feedback: str = "",
    ) -> RapportEquipe:
        """
        Exécute la boucle agentique du chef d'équipe.

        Args:
            client:    Instance Anthropic partagée
            directive: Objectifs précis envoyés par le Superviseur
            contexte:  Contexte de la journée
            feedback:  Retour du Superviseur si révision demandée (vide = 1re exécution)

        Returns:
            RapportEquipe contenant le rapport, les agents recrutés et la confiance
        """
        agents_recrutes: list[str] = []

        feedback_block = ""
        if feedback:
            feedback_block = (
                f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️  FEEDBACK DU SUPERVISEUR — RÉVISION REQUISE :\n"
                f"{feedback}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Intègre ce feedback dans ton rapport révisé."
            )

        messages: list[dict] = [
            {
                "role": "user",
                "content": (
                    f"DIRECTIVE DU SUPERVISEUR :\n{directive}\n\n"
                    f"CONTEXTE DE LA JOURNÉE :\n{contexte}"
                    f"{feedback_block}"
                ),
            }
        ]

        rapport_final = ""
        iterations = 0

        while iterations < self.MAX_ITERATIONS:
            iterations += 1

            response = client.messages.create(
                model=CHEF_MODEL,
                max_tokens=4096,
                system=[
                    {
                        "type": "text",
                        "text": self.system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=[OUTIL_RECRUTEMENT],
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if block.type == "text":
                        rapport_final = block.text
                        break
                break

            messages.append({"role": "assistant", "content": response.content})

            tool_results: list[dict] = []
            for block in response.content:
                if block.type == "tool_use" and block.name == "recruter_agent_specialise":
                    inp = block.input
                    nom_recrute = inp["nom_agent"]

                    logger.chef_recrute(self.nom, nom_recrute, inp["specialite"])
                    agents_recrutes.append(nom_recrute)

                    resultat_worker = run_worker(
                        client=client,
                        nom=nom_recrute,
                        specialite=inp["specialite"],
                        tache=inp["tache"],
                        contexte=inp["contexte"],
                        tools=self.worker_tools or None,
                    )

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": (
                                f"RAPPORT DE L'AGENT {nom_recrute.upper()} :\n"
                                f"{resultat_worker}"
                            ),
                        }
                    )

            if tool_results:
                messages.append({"role": "user", "content": tool_results})
            else:
                # Aucun outil et pas end_turn — sortie de sécurité
                logger.warn(f"Chef {self.nom} : aucun outil appelé sans end_turn — arrêt itération {iterations}")
                break

        # Extraire le niveau de confiance si le chef l'a indiqué
        confidence = _parse_confidence(rapport_final)

        return RapportEquipe(
            rapport=rapport_final,
            agents_recrutes=agents_recrutes,
            confidence=confidence,
        )


# ─── Utilitaire : extraction du niveau de confiance ──────────────────────────

def _parse_confidence(text: str) -> int:
    """Extrait le niveau de confiance (0-100) du rapport si mentionné."""
    import re
    patterns = [
        r"niveau de confiance[^\d]*(\d{1,3})\s*%",
        r"confiance[^\d]*(\d{1,3})\s*%",
        r"confidence[^\d]*(\d{1,3})\s*%",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = int(match.group(1))
            if 0 <= val <= 100:
                return val
    return 80  # valeur par défaut
