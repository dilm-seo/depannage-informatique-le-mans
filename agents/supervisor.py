"""
Superviseur IA — orchestrateur principal avec boucle d'auto-évaluation.

Flux de chaque session :
  0. BILAN     — Lit les stats CRM, injecte dans le contexte
  1. OBJECTIFS — Fixe des objectifs mesurables pour cette session
  2. DIRECTIVES — Envoie une directive adaptée à chaque chef d'équipe
  3. VALIDATION — Évalue chaque rapport, demande révision si nécessaire
  4. COACHING  — Identifie un point d'amélioration par chef, enregistre
  5. COMPILATION — Compile le rapport final (usage interne)
  6. TELEGRAM   — Envoie le résumé concis à Etienne (chiffres + alertes)
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
from agents.tools import crm, telegram

# ─── Outils du Superviseur ────────────────────────────────────────────────────

TOOLS_SUPERVISEUR: list[dict] = [
    {
        "name": "deleguer_mission",
        "description": (
            "Délègue une mission à un chef d'équipe avec une directive précise. "
            "Le chef d'équipe peut recruter ses propres agents spécialisés. "
            "Utilise cet outil pour chaque chef d'équipe avant d'évaluer son travail."
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
                        "Inclure les objectifs de session et les points d'amélioration identifiés."
                    ),
                },
                "contexte": {
                    "type": "string",
                    "description": "Contexte journalier pertinent pour cette mission (inclure stats CRM)",
                },
            },
            "required": ["agent", "directive", "contexte"],
        },
    },
    {
        "name": "envoyer_feedback",
        "description": (
            "Envoie un feedback constructif à un chef d'équipe pour lui demander "
            "de réviser son rapport. Max 1 feedback par agent par session."
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
                    "description": "Feedback précis : ce qui manque, ce qui doit être corrigé.",
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
        "name": "enregistrer_coaching",
        "description": (
            "Enregistre un point d'amélioration identifié lors de l'évaluation des rapports. "
            "À appeler après l'évaluation de chaque rapport pour alimenter l'apprentissage continu. "
            "Ces améliorations seront utilisées dès la prochaine session."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "amelioration": {
                    "type": "string",
                    "description": (
                        "Point d'amélioration concret et actionnable. "
                        "Exemples : 'Secteur BTP génère 0% de réponse, pivoter vers santé', "
                        "'Objet email trop générique, personnaliser par métier'"
                    ),
                },
            },
            "required": ["amelioration"],
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
                    "description": "Ta synthèse personnelle : observations transversales, priorités.",
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
    {
        "name": "envoyer_resume_telegram",
        "description": (
            "Envoie le résumé de session à Etienne sur Telegram. "
            "À appeler UNE SEULE FOIS à la toute fin, après compilation du rapport. "
            "Inclure les vrais chiffres de la session (emails envoyés, relances, etc.)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "emails_envoyes": {"type": "integer", "description": "Nombre d'emails envoyés cette session"},
                "secteurs": {"type": "array", "items": {"type": "string"}, "description": "Secteurs prospectés"},
                "nouvelles_entreprises_sirene": {"type": "integer", "description": "Nouvelles entreprises SIRENE contactées"},
                "relances": {"type": "integer", "description": "Nombre de relances effectuées"},
                "total_crm": {"type": "integer", "description": "Total de contacts dans le CRM"},
                "taux_reponse": {"type": "number", "description": "Taux de réponse actuel en %"},
                "amelioration_identifiee": {"type": "string", "description": "Un point d'amélioration concret pour la prochaine session"},
                "alerte": {"type": "string", "description": "Alerte si prospect a répondu ou urgence (vide sinon)"},
            },
            "required": ["emails_envoyes", "secteurs", "nouvelles_entreprises_sirene", "relances", "total_crm", "taux_reponse", "amelioration_identifiee"],
        },
    },
    {
        "name": "envoyer_alerte_telegram",
        "description": (
            "Envoie une alerte urgente à Etienne. "
            "Utiliser UNIQUEMENT si un prospect a répondu ou si un problème critique est détecté."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message d'alerte concis et actionnable"},
            },
            "required": ["message"],
        },
    },
]


# ─── Classe Superviseur ───────────────────────────────────────────────────────

class Superviseur:
    """
    Orchestrateur principal.

    Maintient l'état des rapports validés et exécute la boucle agentique
    jusqu'à la compilation du rapport final et l'envoi du résumé Telegram.
    """

    MAX_ITERATIONS = 25  # 3 agents × (délégation + feedback + révision) + coaching + final + telegram

    def __init__(self) -> None:
        self.client = anthropic.Anthropic()
        self._chefs = {
            "planification": ChefEquipePlanification(),
            "prospection":   ChefEquipeProspection(),
            "strategie":     ChefEquipeStrategie(),
        }
        self._chef_rapport = ChefEquipeRapport()
        self._rapports_valides: dict[str, str] = {}
        self._feedbacks_envoyes: set[str] = set()

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
                self._rapports_valides[agent_nom] = result.rapport
                recrutes = ", ".join(result.agents_recrutes) or "aucun"
                logger.supervisor_recu(agent_nom.upper(), result.confidence, recrutes)
                return (
                    f"RAPPORT DU CHEF {agent_nom.upper()} reçu.\n"
                    f"Agents recrutés : {recrutes}\n"
                    f"Niveau de confiance : {result.confidence} %\n\n"
                    f"─── CONTENU DU RAPPORT ───\n"
                    f"{result.rapport}"
                )

            case "envoyer_feedback":
                agent_nom = inputs["agent"]
                if agent_nom in self._feedbacks_envoyes:
                    return (
                        f"[SYSTÈME] Feedback déjà envoyé à {agent_nom}. "
                        f"Utilise le rapport existant."
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
                self._rapports_valides[agent_nom] = result.rapport
                recrutes = ", ".join(result.agents_recrutes) or "aucun"
                logger.supervisor_recu(agent_nom.upper(), result.confidence, recrutes)
                return (
                    f"RAPPORT RÉVISÉ DU CHEF {agent_nom.upper()} reçu.\n"
                    f"Agents lors de la révision : {recrutes}\n"
                    f"Niveau de confiance : {result.confidence} %\n\n"
                    f"─── RAPPORT RÉVISÉ ───\n"
                    f"{result.rapport}"
                )

            case "enregistrer_coaching":
                amelioration = inputs["amelioration"]
                logger.supervisor(f"📝 Coaching enregistré : {amelioration[:80]}")
                return crm.enregistrer_amelioration(amelioration)

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

            case "envoyer_resume_telegram":
                logger.supervisor("📊 Envoi résumé Telegram à Etienne…")
                return telegram.envoyer_resume_session(
                    emails_envoyes=inputs["emails_envoyes"],
                    secteurs=inputs["secteurs"],
                    nouvelles_entreprises_sirene=inputs["nouvelles_entreprises_sirene"],
                    relances=inputs["relances"],
                    total_crm=inputs["total_crm"],
                    taux_reponse=inputs["taux_reponse"],
                    amelioration_identifiee=inputs["amelioration_identifiee"],
                    alerte=inputs.get("alerte", ""),
                )

            case "envoyer_alerte_telegram":
                logger.supervisor(f"🚨 Alerte Telegram : {inputs['message'][:80]}")
                return telegram.envoyer_alerte(inputs["message"])

            case _:
                return f"[ERREUR] Outil inconnu : {name}"

    # ─── Boucle principale ────────────────────────────────────────────────────

    def run(self, contexte_journee: str = "") -> str:
        """
        Lance la supervision complète de la journée.

        1. Charge les stats CRM pour l'auto-évaluation
        2. Envoie des directives adaptées à chaque chef d'équipe
        3. Évalue et valide (ou révise) chaque rapport
        4. Enregistre les points de coaching
        5. Compile le compte-rendu final
        6. Envoie le résumé Telegram à Etienne

        Returns:
            Rapport journalier complet en Markdown
        """
        today = date.today()
        jours_fr = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
        mois_fr  = ["janvier", "février", "mars", "avril", "mai", "juin",
                    "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
        date_fr = f"{jours_fr[today.weekday()]} {today.day} {mois_fr[today.month - 1]} {today.year}"

        logger.divider(f"SUPERVISEUR — {date_fr.upper()}")

        # Charger le bilan CRM pour l'auto-évaluation
        bilan_crm = crm.get_resume_performance()
        relances_jour = crm.get_relances_du_jour()
        logger.supervisor(f"Bilan CRM chargé — {len(relances_jour)} relance(s) prévue(s) aujourd'hui")

        contexte_complet = (
            f"DATE : {date_fr}\n\n"
            f"═══════════ BILAN CRM (AUTO-ÉVALUATION) ═══════════\n"
            f"{bilan_crm}\n"
            f"Relances à effectuer aujourd'hui : {len(relances_jour)} prospect(s)\n\n"
        )
        if contexte_journee:
            contexte_complet += f"═══════════ CONTEXTE ADDITIONNEL ═══════════\n{contexte_journee}\n\n"
        if relances_jour:
            noms_relances = ", ".join(r["nom"] for r in relances_jour[:5])
            contexte_complet += f"Prospects à relancer : {noms_relances}\n"

        messages: list[dict] = [
            {
                "role": "user",
                "content": (
                    f"Nous sommes le {date_fr}.\n\n"
                    f"{contexte_complet}\n"
                    f"Lance ton processus de supervision autonome :\n"
                    f"1. BILAN — Analyse les stats CRM ci-dessus\n"
                    f"2. OBJECTIFS — Fixe des objectifs précis pour cette session\n"
                    f"3. DIRECTIVES — Envoie une directive adaptée à chaque chef\n"
                    f"4. VALIDATION — Évalue chaque rapport, demande révision si besoin\n"
                    f"5. COACHING — Enregistre un point d'amélioration (enregistrer_coaching)\n"
                    f"6. COMPILATION — Compile le rapport final\n"
                    f"7. TELEGRAM — Envoie le résumé à Etienne (envoyer_resume_telegram)\n\n"
                    f"Commence maintenant. Tu travailles en totale autonomie."
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

        if not rapport_final and "rapport_final" in self._rapports_valides:
            rapport_final = self._rapports_valides["rapport_final"]

        if not rapport_final:
            rapport_final = (
                "⚠️  Le rapport final n'a pas pu être généré automatiquement.\n"
                "Relancez le système ou vérifiez votre clé API."
            )

        logger.divider("SUPERVISION TERMINÉE")
        return rapport_final
