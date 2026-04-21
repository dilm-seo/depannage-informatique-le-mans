"""
Superviseur IA — orchestrateur principal avec flux bidirectionnel.

Flux pour chaque chef d'équipe :
  1. Superviseur → DIRECTIVE précise (objectifs + critères de succès)
  2. Chef d'équipe → travaille, recrute des agents si besoin
  3. Chef d'équipe → RAPPORT au Superviseur (avec liste agents recrutés)
  4. Superviseur → ÉVALUE : valide OU demande révision avec feedback
  5. (si révision) Chef d'équipe → rapport révisé
  6. Superviseur → COMPILE le rapport final une fois tout validé
"""

from __future__ import annotations

from datetime import date

import anthropic

from agents.config import SUPERVISOR_MODEL, SUPERVISOR_SYSTEM, BUSINESS
from agents.sub_agents.planification import ChefEquipePlanification
from agents.sub_agents.prospection   import ChefEquipeProspection
from agents.sub_agents.strategie     import ChefEquipeStrategie
from agents.sub_agents.rapport       import ChefEquipeRapport
from agents.utils import logger

# ─── Outils du Superviseur ────────────────────────────────────────────────────

TOOLS_SUPERVISEUR: list[dict] = [
    {
        "name": "deleguer_mission",
        "description": (
            "Délègue une mission à un chef d'équipe avec une directive précise. "
            "Le chef d'équipe peut recruter ses propres agents spécialisés, "
            "puis rend compte avec son rapport et la liste des agents qu'il a utilisés. "
            "Utilise cet outil pour chaque agent avant d'évaluer son travail."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "enum": ["planification", "prospection", "strategie"],
                    "description": "Le chef d'équipe à qui déléguer la mission",
                },
                "directive": {
                    "type": "string",
                    "description": (
                        "Directive précise avec objectifs clairs et critères de succès mesurables. "
                        "Exemple : 'Crée un planning géographiquement optimisé pour 3 interventions "
                        "Le Mans nord + 1 urgence récupération données à La Flèche. "
                        "Critères : créneaux de prospection inclus, temps trajet estimé.'"
                    ),
                },
                "contexte": {
                    "type": "string",
                    "description": "Partie du contexte journalier pertinente pour cette mission",
                },
            },
            "required": ["agent", "directive", "contexte"],
        },
    },
    {
        "name": "envoyer_feedback",
        "description": (
            "Envoie un feedback constructif à un chef d'équipe pour lui demander "
            "de réviser son rapport. Utilise quand le rapport ne satisfait pas "
            "un ou plusieurs critères de ta directive. Max 1 feedback par agent."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "enum": ["planification", "prospection", "strategie"],
                },
                "feedback": {
                    "type": "string",
                    "description": (
                        "Feedback précis et constructif : ce qui manque, "
                        "ce qui doit être corrigé ou approfondi."
                    ),
                },
                "directive_originale": {
                    "type": "string",
                    "description": "La directive originale envoyée à cet agent",
                },
                "contexte": {
                    "type": "string",
                    "description": "Le même contexte que lors de la délégation initiale",
                },
            },
            "required": ["agent", "feedback", "directive_originale", "contexte"],
        },
    },
    {
        "name": "compiler_rapport_final",
        "description": (
            "Compile les trois rapports validés en un compte-rendu journalier final "
            "structuré en Markdown. Appelle cet outil UNIQUEMENT quand les trois chefs "
            "d'équipe ont rendu leurs rapports approuvés."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "contexte_general": {
                    "type": "string",
                    "description": "Le contexte journalier complet fourni initialement",
                },
                "rapport_planification": {
                    "type": "string",
                    "description": "Rapport validé du Chef Planification",
                },
                "rapport_prospection": {
                    "type": "string",
                    "description": "Rapport validé du Chef Prospection",
                },
                "rapport_strategie": {
                    "type": "string",
                    "description": "Rapport validé du Chef Stratégie",
                },
                "synthese_superviseur": {
                    "type": "string",
                    "description": (
                        "Ta synthèse personnelle : observations transversales, "
                        "priorités absolues, messages clés de la journée."
                    ),
                },
            },
            "required": [
                "contexte_general",
                "rapport_planification",
                "rapport_prospection",
                "rapport_strategie",
            ],
        },
    },
]


# ─── Classe Superviseur ───────────────────────────────────────────────────────

class Superviseur:
    """
    Orchestrateur principal.

    Maintient l'état des rapports validés et exécute la boucle agentique
    jusqu'à la compilation du rapport final.
    """

    MAX_ITERATIONS = 20  # garde-fou : 3 agents × (délégation + feedback + révision) + final

    def __init__(self) -> None:
        self.client = anthropic.Anthropic()
        self._chefs = {
            "planification": ChefEquipePlanification(),
            "prospection":   ChefEquipeProspection(),
            "strategie":     ChefEquipeStrategie(),
        }
        self._chef_rapport = ChefEquipeRapport()
        # État interne — rapports validés par le Superviseur
        self._rapports_valides: dict[str, str] = {}
        self._feedbacks_envoyes: set[str] = set()   # un seul feedback max par agent

    # ─── Exécution des outils ─────────────────────────────────────────────────

    def _execute_tool(self, name: str, inputs: dict) -> str:
        match name:

            case "deleguer_mission":
                agent_nom = inputs["agent"]
                chef = self._chefs[agent_nom]

                logger.supervisor_delegue(agent_nom.upper(), inputs["directive"])

                result = chef.run(
                    client=self.client,
                    directive=inputs["directive"],
                    contexte=inputs["contexte"],
                )

                # Mémoriser le rapport pour la compilation finale
                self._rapports_valides[agent_nom] = result.rapport

                recrutes = ", ".join(result.agents_recrutes) or "aucun"
                logger.supervisor_recu(agent_nom.upper(), result.confidence, recrutes)

                return (
                    f"RAPPORT DU CHEF {agent_nom.upper()} reçu.\n"
                    f"Agents recrutés par ce chef : {recrutes}\n"
                    f"Niveau de confiance déclaré : {result.confidence} %\n\n"
                    f"─── CONTENU DU RAPPORT ───\n"
                    f"{result.rapport}"
                )

            case "envoyer_feedback":
                agent_nom = inputs["agent"]

                if agent_nom in self._feedbacks_envoyes:
                    return (
                        f"[SYSTÈME] Feedback déjà envoyé à {agent_nom}. "
                        f"Utilise le rapport existant ou valide-le tel quel."
                    )

                self._feedbacks_envoyes.add(agent_nom)
                chef = self._chefs[agent_nom]

                logger.supervisor_feedback(agent_nom.upper(), inputs["feedback"])

                result = chef.run(
                    client=self.client,
                    directive=inputs["directive_originale"],
                    contexte=inputs["contexte"],
                    feedback=inputs["feedback"],
                )

                # Mise à jour du rapport avec la version révisée
                self._rapports_valides[agent_nom] = result.rapport

                recrutes = ", ".join(result.agents_recrutes) or "aucun"
                logger.supervisor_recu(agent_nom.upper(), result.confidence, recrutes)

                return (
                    f"RAPPORT RÉVISÉ DU CHEF {agent_nom.upper()} reçu.\n"
                    f"Agents recrutés lors de la révision : {recrutes}\n"
                    f"Niveau de confiance : {result.confidence} %\n\n"
                    f"─── RAPPORT RÉVISÉ ───\n"
                    f"{result.rapport}"
                )

            case "compiler_rapport_final":
                logger.supervisor("Compilation du rapport final en cours…")

                rapport_final = self._chef_rapport.compiler(
                    client=self.client,
                    rapport_planification=inputs["rapport_planification"],
                    rapport_prospection=inputs["rapport_prospection"],
                    rapport_strategie=inputs["rapport_strategie"],
                    contexte_general=inputs["contexte_general"],
                    synthese_superviseur=inputs.get("synthese_superviseur", ""),
                )

                return rapport_final

            case _:
                return f"[ERREUR] Outil inconnu : {name}"

    # ─── Boucle principale ────────────────────────────────────────────────────

    def run(self, contexte_journee: str) -> str:
        """
        Lance la supervision complète de la journée.

        1. Envoie des directives à chaque chef d'équipe
        2. Évalue et valide (ou révise) chaque rapport
        3. Compile le compte-rendu final

        Returns:
            Rapport journalier complet en Markdown
        """
        today = date.today()
        jours_fr = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
        mois_fr  = ["janvier", "février", "mars", "avril", "mai", "juin",
                    "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
        date_fr = f"{jours_fr[today.weekday()]} {today.day} {mois_fr[today.month - 1]} {today.year}"

        logger.divider(f"SUPERVISEUR — {date_fr.upper()}")

        messages: list[dict] = [
            {
                "role": "user",
                "content": (
                    f"Nous sommes le {date_fr}.\n\n"
                    f"CONTEXTE DE LA JOURNÉE :\n{contexte_journee}\n\n"
                    f"Lance ton processus de supervision :\n"
                    f"1. Analyse le contexte et définis les priorités\n"
                    f"2. Envoie des DIRECTIVES PRÉCISES à chaque chef d'équipe\n"
                    f"3. ÉVALUE chaque rapport reçu — valide ou demande révision\n"
                    f"4. Une fois les 3 rapports validés, compile le rapport final\n\n"
                    f"Commence maintenant."
                ),
            }
        ]

        rapport_final = ""
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
                tools=TOOLS_SUPERVISEUR,
                messages=messages,
            )

            logger.supervisor(
                f"Itération {iterations}/{self.MAX_ITERATIONS} "
                f"— stop_reason={response.stop_reason} "
                f"— {len([b for b in response.content if b.type == 'tool_use'])} outil(s)"
            )

            # Afficher les blocs texte (raisonnement visible du superviseur)
            for block in response.content:
                if block.type == "text" and block.text.strip():
                    for ligne in block.text.strip().splitlines()[:3]:
                        logger.supervisor(f"  › {ligne}")

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if block.type == "text":
                        rapport_final = block.text
                        break
                if not rapport_final and "rapport_final" in self._rapports_valides:
                    rapport_final = self._rapports_valides["rapport_final"]
                break

            messages.append({"role": "assistant", "content": response.content})

            tool_results: list[dict] = []
            for block in response.content:
                if block.type == "tool_use":
                    result_text = self._execute_tool(block.name, block.input)

                    # Si c'est le rapport final compilé, le stocker
                    if block.name == "compiler_rapport_final":
                        rapport_final = result_text
                        self._rapports_valides["rapport_final"] = result_text

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        }
                    )

            if tool_results:
                messages.append({"role": "user", "content": tool_results})
            else:
                logger.warn("Superviseur : aucun outil appelé, stop_reason non end_turn — arrêt")
                break

        # Fallback : si le rapport final est dans les rapports mémorisés
        if not rapport_final and "rapport_final" in self._rapports_valides:
            rapport_final = self._rapports_valides["rapport_final"]

        if not rapport_final:
            rapport_final = (
                "⚠️  Le rapport final n'a pas pu être généré automatiquement.\n"
                "Relancez le système ou vérifiez votre clé API."
            )

        logger.divider("SUPERVISION TERMINÉE")
        return rapport_final
