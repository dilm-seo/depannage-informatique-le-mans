"""
Agent Travailleur — factory générique d'agents spécialisés.

Un agent travailleur est recruté dynamiquement par un chef d'équipe pour
accomplir une tâche précise et délimitée. Il ne peut pas recruter d'autres
agents (nœud feuille de la hiérarchie).

Quand des outils sont fournis, l'agent exécute une boucle agentique
pour utiliser ces outils avant de produire son résultat final.
"""

from __future__ import annotations

import anthropic

from agents.config import WORKER_MODEL, WORKER_SYSTEM_TEMPLATE, BUSINESS
from agents.utils import logger

_MAX_TOOL_ITERATIONS = 15  # suffisant pour : SIRENE → vérif CRM × N → emails × N → CRM


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
        nom:        Nom du rôle de l'agent  (ex: "Chercheur SIRENE")
        specialite: Domaine d'expertise     (ex: "prospection SIRENE")
        tache:      Description précise de la mission à accomplir
        contexte:   Informations contextuelles nécessaires à l'agent
        tools:      Outils disponibles. None = mode simple sans tools.

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

    if tools:
        tool_names = "\n  • ".join(
            f"{t['name']} — {t['description'][:80]}" for t in tools
        )
        system_text += (
            f"\n\nOUTILS DISPONIBLES :\n  • {tool_names}\n\n"
            f"ORDRE D'UTILISATION OBLIGATOIRE POUR CHAQUE PROSPECT :\n"
            f"  1. crm_verifier_prospect → 2. envoyer_email_prospect → 3. crm_ajouter_prospect\n"
            f"Effectue au minimum 3 cycles complets avant de rédiger ton rapport."
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
        response = client.messages.create(
            model=WORKER_MODEL,
            max_tokens=2048,
            system=system_block,
            messages=messages,
        )
        result = response.content[0].text
        logger.worker(tag, f"Mission accomplie — {len(result)} caractères")
        return result

    return _run_agentic(client, tag, system_block, messages, tools)


def _run_agentic(
    client: anthropic.Anthropic,
    tag: str,
    system_block: list[dict],
    messages: list[dict],
    tools: list[dict],
) -> str:
    """Boucle agentique pour les workers avec accès aux outils."""
    from agents.tools.web_search import rechercher_web, rechercher_entreprises_local
    from agents.tools import crm as crm_module
    from agents.tools import sirene as sirene_module
    from agents.tools import telegram as telegram_module

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

            tool_output = _execute_worker_tool(block.name, block.input, tag,
                                               rechercher_web, rechercher_entreprises_local,
                                               crm_module, sirene_module, telegram_module)

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


def _execute_worker_tool(
    name: str,
    inputs: dict,
    tag: str,
    rechercher_web,
    rechercher_entreprises_local,
    crm_module,
    sirene_module,
    telegram_module,
) -> str:
    match name:

        case "rechercher_web":
            query = inputs["query"]
            max_r = inputs.get("max_results", 8)
            logger.worker(tag, f"🔍 Web : {query[:70]}")
            return rechercher_web(query, max_r)

        case "rechercher_entreprises_local":
            secteur = inputs["secteur"]
            ville = inputs.get("ville", "Le Mans")
            logger.worker(tag, f"🏢 Prospects : {secteur} à {ville}")
            return rechercher_entreprises_local(secteur, ville)

        case "chercher_nouvelles_entreprises_sirene":
            jours = inputs.get("jours", 30)
            naf = inputs.get("secteur_naf", "")
            max_r = inputs.get("max_resultats", 10)
            label = f"NAF={naf}" if naf else "tous secteurs"
            logger.worker(tag, f"🏭 SIRENE Sarthe — {label} — {jours}j")
            return sirene_module.chercher_nouvelles_entreprises(
                departement="72",
                jours=jours,
                secteur_naf=naf,
                max_resultats=max_r,
            )

        case "crm_verifier_prospect":
            tel = inputs.get("telephone", "")
            email = inputs.get("email", "")
            deja = crm_module.est_deja_contacte(tel, email)
            if deja:
                logger.worker(tag, f"🔴 CRM : déjà contacté ({tel or email})")
                return "déjà_contacté — passer au prospect suivant"
            logger.worker(tag, f"🟢 CRM : nouveau prospect ({tel or email})")
            return "nouveau — ce prospect peut être contacté"

        case "crm_ajouter_prospect":
            nom = inputs.get("nom_entreprise", "")
            logger.worker(tag, f"💾 CRM : ajout {nom[:40]}")
            return crm_module.ajouter_prospect(
                nom_entreprise=nom,
                secteur=inputs.get("secteur", ""),
                telephone=inputs.get("telephone", ""),
                email=inputs.get("email", ""),
                source=inputs.get("source", "web"),
                message_envoye=inputs.get("message_envoye", ""),
                canal=inputs.get("canal", "email"),
            )

        case "crm_get_stats":
            return crm_module.get_resume_performance()

        case "envoyer_email_prospect":
            from agents.tools.email import envoyer_email_prospect
            inp = inputs
            logger.worker(tag, f"📧 Email → {inp['destinataire_nom']} <{inp['destinataire_email']}>")
            return envoyer_email_prospect(
                destinataire_email=inp["destinataire_email"],
                destinataire_nom=inp["destinataire_nom"],
                sujet=inp["sujet"],
                corps=inp["corps"],
            )

        case "envoyer_alerte_telegram":
            logger.worker(tag, f"🚨 Alerte Telegram")
            return telegram_module.envoyer_alerte(inputs["message"])

        case _:
            return f"[ERREUR] Outil inconnu : {name}"
