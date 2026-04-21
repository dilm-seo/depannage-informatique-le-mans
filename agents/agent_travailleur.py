"""
Agent Travailleur — factory générique d'agents spécialisés.

Un agent travailleur est recruté dynamiquement par un chef d'équipe pour
accomplir une tâche précise et délimitée. Il ne peut pas recruter d'autres
agents (nœud feuille de la hiérarchie).

Quand des outils sont fournis (ex: recherche web), l'agent exécute une boucle
agentique pour utiliser ces outils avant de produire son résultat final.
"""

from __future__ import annotations

import anthropic

from agents.config import WORKER_MODEL, WORKER_SYSTEM_TEMPLATE, BUSINESS
from agents.utils import logger

_MAX_TOOL_ITERATIONS = 6


def run(
    client: anthropic.Anthropic,
    nom: str,
    specialite: str,
    tache: str,
    contexte: str,
    tools: list[dict] | None = None,
) -> str:
    """
    Crée et exécute un agent travailleur spécialisé.

    Args:
        client:     Instance Anthropic partagée
        nom:        Nom du rôle de l'agent  (ex: "Chercheur de Prospects")
        specialite: Domaine d'expertise     (ex: "recherche de prospects locaux")
        tache:      Description précise de la mission à accomplir
        contexte:   Informations contextuelles nécessaires à l'agent
        tools:      Outils disponibles (ex: web search). None = mode simple sans tools.

    Returns:
        Résultat formaté en texte Markdown
    """
    tag = f"TRAVAILLEUR › {nom[:28]}"
    tool_hint = f" [+{len(tools)} outil(s)]" if tools else ""
    logger.worker(tag, f"{tache[:90]}…{tool_hint}")

    system_text = WORKER_SYSTEM_TEMPLATE.format(
        nom=nom,
        specialite=specialite,
        business_name=BUSINESS["name"],
        website=BUSINESS["website"],
    )

    # Informer l'agent de ses outils disponibles
    if tools:
        tool_names = "\n  • ".join(
            f"{t['name']} — {t['description'][:80]}" for t in tools
        )
        system_text += (
            f"\n\nOUTILS WEB À TA DISPOSITION :\n  • {tool_names}\n\n"
            f"Utilise ces outils pour obtenir des données RÉELLES et actuelles. "
            f"Effectue plusieurs recherches ciblées avant de rédiger ton rapport."
        )

    system_block = [
        {
            "type": "text",
            "text": system_text,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                f"TÂCHE ASSIGNÉE PAR TON CHEF D'ÉQUIPE :\n{tache}\n\n"
                f"CONTEXTE :\n{contexte}"
            ),
        }
    ]

    if not tools:
        # Mode simple : un seul appel API, pas de tool use
        response = client.messages.create(
            model=WORKER_MODEL,
            max_tokens=2048,
            system=system_block,
            messages=messages,
        )
        result = response.content[0].text
        logger.worker(tag, f"Mission accomplie — {len(result)} caractères")
        return result

    # Mode agentique : boucle avec tool use (web search, etc.)
    return _run_agentic(client, tag, system_block, messages, tools)


def _run_agentic(
    client: anthropic.Anthropic,
    tag: str,
    system_block: list[dict],
    messages: list[dict],
    tools: list[dict],
) -> str:
    """Boucle agentique pour les workers avec accès aux outils web."""
    from agents.tools.web_search import rechercher_web, rechercher_entreprises_local

    result = ""

    for iteration in range(_MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model=WORKER_MODEL,
            max_tokens=4096,
            system=system_block,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    result = block.text
                    break
            break

        messages.append({"role": "assistant", "content": response.content})

        tool_results: list[dict] = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            if block.name == "rechercher_web":
                query = block.input["query"]
                max_r = block.input.get("max_results", 8)
                logger.worker(tag, f"🔍 Recherche : {query[:70]}")
                tool_output = rechercher_web(query, max_r)

            elif block.name == "rechercher_entreprises_local":
                secteur = block.input["secteur"]
                ville = block.input.get("ville", "Le Mans")
                logger.worker(tag, f"🏢 Prospects : {secteur} à {ville}")
                tool_output = rechercher_entreprises_local(secteur, ville)

            elif block.name == "envoyer_email_prospect":
                from agents.tools.email import envoyer_email_prospect
                inp = block.input
                logger.worker(tag, f"📧 Email → {inp['destinataire_nom']} <{inp['destinataire_email']}>")
                tool_output = envoyer_email_prospect(
                    destinataire_email=inp["destinataire_email"],
                    destinataire_nom=inp["destinataire_nom"],
                    sujet=inp["sujet"],
                    corps=inp["corps"],
                )

            elif block.name == "envoyer_prospect_telegram":
                from agents.tools.telegram import envoyer_prospect
                inp = block.input
                logger.worker(tag, f"📱 Telegram → {inp['nom_entreprise']} ({inp['telephone']})")
                tool_output = envoyer_prospect(
                    nom_entreprise=inp["nom_entreprise"],
                    secteur=inp["secteur"],
                    telephone=inp["telephone"],
                    message_a_envoyer=inp["message_a_envoyer"],
                    priorite=inp.get("priorite", "normale"),
                )

            else:
                tool_output = f"[ERREUR] Outil inconnu : {block.name}"

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": tool_output,
            })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            logger.warn(f"Worker {tag} : aucun outil sans end_turn — arrêt itération {iteration + 1}")
            break

    # Fallback : récupérer le dernier bloc texte si la boucle n'a pas produit de résultat
    if not result:
        for msg in reversed(messages):
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if hasattr(block, "type") and block.type == "text" and block.text.strip():
                        result = block.text
                        break
            if result:
                break

    logger.worker(tag, f"Mission accomplie — {len(result)} caractères")
    return result
