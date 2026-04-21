"""Agent Superviseur — orchestrateur principal du système multi-agents."""

import json
from datetime import date

import anthropic

from agents.config import SUPERVISOR_MODEL, SUPERVISOR_SYSTEM, BUSINESS
from agents.utils import logger
from agents.sub_agents import planification, prospection, strategie, rapport


# ─── Définition des outils du superviseur ────────────────────────────────────
TOOLS: list[dict] = [
    {
        "name": "agent_planification",
        "description": (
            "Agent spécialisé en organisation et planning journalier. "
            "Il crée un planning optimisé géographiquement, priorise les tâches "
            "par urgence et rentabilité, et intègre des créneaux de prospection."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "contexte": {
                    "type": "string",
                    "description": (
                        "Contexte et informations pertinentes pour la planification : "
                        "interventions en cours, rendez-vous, urgences signalées, zones géographiques"
                    ),
                },
                "priorites": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Liste des priorités ou tâches importantes du jour",
                },
            },
            "required": ["contexte"],
        },
    },
    {
        "name": "agent_prospection",
        "description": (
            "Agent spécialisé en développement commercial et acquisition clients. "
            "Il identifie des leads, propose des actions de prospection concrètes, "
            "des scripts de contact et des objectifs commerciaux pour la journée."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "contexte": {
                    "type": "string",
                    "description": (
                        "Contexte commercial actuel : pipeline existant, clients récents, "
                        "actions de prospection précédentes, résultats obtenus"
                    ),
                },
                "focus": {
                    "type": "string",
                    "description": (
                        "Type de prospection à privilégier : "
                        "'nouveaux_clients', 'fidelisation', 'partenariats', 'b2b', 'seniors', etc."
                    ),
                },
            },
            "required": ["contexte"],
        },
    },
    {
        "name": "agent_strategie",
        "description": (
            "Agent spécialisé en analyse stratégique et conseil en développement d'entreprise. "
            "Il réalise une analyse SWOT, identifie des opportunités de croissance, "
            "surveille la concurrence et propose des recommandations à court et moyen terme."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "contexte": {
                    "type": "string",
                    "description": (
                        "Situation actuelle de l'entreprise, défis identifiés, "
                        "opportunités perçues, points à analyser en priorité"
                    ),
                },
                "questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Questions stratégiques spécifiques à adresser",
                },
            },
            "required": ["contexte"],
        },
    },
    {
        "name": "agent_rapport",
        "description": (
            "Agent spécialisé en synthèse et reporting. "
            "Il compile les résultats de tous les agents et génère le compte-rendu "
            "journalier final, complet et directement actionnable."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "planning": {
                    "type": "string",
                    "description": "Résultat complet de l'agent planification",
                },
                "prospection": {
                    "type": "string",
                    "description": "Résultat complet de l'agent prospection",
                },
                "strategie": {
                    "type": "string",
                    "description": "Résultat complet de l'agent stratégie",
                },
                "contexte_general": {
                    "type": "string",
                    "description": "Contexte général de la journée tel que fourni initialement",
                },
            },
            "required": ["planning", "prospection", "strategie", "contexte_general"],
        },
    },
]


class Superviseur:
    """Orchestrateur principal qui gère les agents spécialisés via l'API tool use."""

    MAX_ITERATIONS = 10  # garde-fou anti-boucle infinie

    def __init__(self) -> None:
        self.client = anthropic.Anthropic()

    def _execute_tool(self, name: str, inputs: dict) -> str:
        """Dispatche l'appel vers le bon sous-agent et retourne son résultat."""
        match name:
            case "agent_planification":
                return planification.run(
                    self.client,
                    contexte=inputs["contexte"],
                    priorites=inputs.get("priorites"),
                )
            case "agent_prospection":
                return prospection.run(
                    self.client,
                    contexte=inputs["contexte"],
                    focus=inputs.get("focus", ""),
                )
            case "agent_strategie":
                return strategie.run(
                    self.client,
                    contexte=inputs["contexte"],
                    questions=inputs.get("questions"),
                )
            case "agent_rapport":
                return rapport.run(
                    self.client,
                    planning=inputs["planning"],
                    prospection=inputs["prospection"],
                    strategie=inputs["strategie"],
                    contexte_general=inputs["contexte_general"],
                )
            case _:
                return f"[ERREUR] Outil inconnu : {name}"

    def run(self, contexte_journee: str) -> str:
        """
        Lance le superviseur pour gérer la journée complète.

        Args:
            contexte_journee: Description du contexte du jour fournie par l'utilisateur

        Returns:
            Compte-rendu journalier final en Markdown
        """
        today = date.today()
        jours_fr = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
        mois_fr = [
            "janvier", "février", "mars", "avril", "mai", "juin",
            "juillet", "août", "septembre", "octobre", "novembre", "décembre",
        ]
        date_fr = f"{jours_fr[today.weekday()]} {today.day} {mois_fr[today.month - 1]} {today.year}"

        logger.supervisor(f"Démarrage — journée du {date_fr}")
        logger.divider()

        messages: list[dict] = [
            {
                "role": "user",
                "content": (
                    f"Gère ma journée du {date_fr}.\n\n"
                    f"CONTEXTE DU JOUR :\n{contexte_journee}\n\n"
                    "Orchestre tous les agents spécialisés pour :\n"
                    "1. Organiser et optimiser mon planning\n"
                    "2. Identifier des opportunités commerciales et actions de prospection\n"
                    "3. Fournir des insights stratégiques pour développer l'entreprise\n"
                    "4. Compiler le tout en un compte-rendu journalier complet\n\n"
                    "Lance les agents dans l'ordre logique et génère le rapport final."
                ),
            }
        ]

        final_report = ""
        iterations = 0

        while iterations < self.MAX_ITERATIONS:
            iterations += 1

            response = self.client.messages.create(
                model=SUPERVISOR_MODEL,
                max_tokens=8192,
                thinking={"type": "adaptive"},
                system=[
                    {
                        "type": "text",
                        "text": SUPERVISOR_SYSTEM,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=TOOLS,
                messages=messages,
            )

            logger.supervisor(
                f"Itération {iterations} — stop_reason={response.stop_reason}"
            )

            # Collecter les blocs texte éventuels du superviseur
            for block in response.content:
                if block.type == "text" and block.text.strip():
                    logger.supervisor(f"→ {block.text[:120]}...")

            if response.stop_reason == "end_turn":
                # Extraire le texte final (le rapport compilé)
                for block in response.content:
                    if block.type == "text":
                        final_report = block.text
                        break
                break

            # Appender la réponse de l'assistant
            messages.append({"role": "assistant", "content": response.content})

            # Traiter tous les appels d'outils
            tool_results: list[dict] = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.supervisor(f"Délégation → {block.name}")
                    result = self._execute_tool(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )
                    logger.supervisor(
                        f"Résultat reçu de {block.name} ({len(result)} caractères)"
                    )

            if tool_results:
                messages.append({"role": "user", "content": tool_results})
            else:
                # Aucun outil appelé et pas end_turn → sortie de sécurité
                logger.warn("Aucun outil appelé et stop_reason != end_turn — arrêt de sécurité")
                break

        if not final_report:
            logger.warn("Rapport final non trouvé dans la réponse du superviseur")
            final_report = "⚠️ Le rapport final n'a pas pu être généré. Veuillez relancer le système."

        logger.divider()
        logger.supervisor("Journée traitée — rapport disponible")
        return final_report
