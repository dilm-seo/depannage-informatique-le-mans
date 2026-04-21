#!/usr/bin/env python3
"""
Bot Telegram conversationnel — dialogue avec le Superviseur IA Fix72.

Etienne envoie un message depuis son iPhone → réponse en < 5 minutes.

Exemples de questions :
  "Où en est la prospection ?"
  "Que penses-tu du chef prospection ?"
  "Combien d'emails envoyés cette semaine ?"
  "Quelles sont les prochaines actions prioritaires ?"
  "Quel secteur fonctionne le mieux ?"
  "Y a-t-il des relances à faire ?"

Le bot tourne toutes les 5 minutes via GitHub Actions.
L'état (dernier message lu) est conservé dans le cache GitHub Actions.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
load_dotenv()

_STATE_PATH = Path(__file__).parent / "data" / "bot_state.json"

_BOT_SYSTEM = """Tu es le Superviseur IA de Fix72, le système d'agents commerciaux autonomes d'Etienne Aubry.

Etienne te contacte via Telegram pour avoir un point sur la situation.
Tu lui réponds en tant que superviseur de son équipe IA, de façon concise et directe.
Maximum 8-10 lignes. Pas de markdown complexe — texte simple avec émojis si utile.
Tu parles en première personne. Tu es son bras droit commercial IA.

FIX72 : Dépannage informatique Le Mans — 06 64 31 34 74 — fix72.com
Etienne Aubry, technicien certifié Microsoft & CompTIA, 10+ ans d'expérience.

TON ÉQUIPE :
  • Chef Prospection — trouve et contacte des prospects par email (SIRENE + web). Objectif : 5-10 emails/session.
  • Chef Planification — organise les créneaux, priorise les interventions, optimise les itinéraires.
  • Chef Stratégie — analyse performance, concurrence, identifie les opportunités de croissance.

Tu réponds en français, de façon concise, honnête et actionnable.
Si tu ne sais pas quelque chose, dis-le clairement plutôt que d'inventer."""


def _load_state() -> dict:
    if _STATE_PATH.exists():
        try:
            return json.loads(_STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_update_id": 0, "historique": []}


def _save_state(state: dict) -> None:
    _STATE_PATH.parent.mkdir(exist_ok=True)
    _STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _telegram_call(token: str, method: str, params: dict | None = None) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    if params:
        data = json.dumps(params).encode()
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"})
    else:
        req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def _get_updates(token: str, offset: int) -> list[dict]:
    result = _telegram_call(token, "getUpdates", {"offset": offset, "limit": 10, "timeout": 0})
    return result.get("result", [])


def _send_message(token: str, chat_id: str, text: str) -> None:
    for chunk in [text[i:i + 4000] for i in range(0, len(text), 4000)]:
        _telegram_call(token, "sendMessage", {"chat_id": chat_id, "text": chunk})


def _get_crm_context() -> str:
    """Charge les stats CRM pour donner du contexte à Claude."""
    try:
        from agents.tools.crm import get_resume_performance, _load
        stats = get_resume_performance()
        data = _load()
        ameliorations = data.get("ameliorations", [])
        derniere_session = data.get("derniere_session", "Aucune session encore")
        amelio_str = (
            "\n".join(f"  - {a}" for a in ameliorations[-3:])
            if ameliorations else "  Aucune encore"
        )
        return (
            f"{stats}\n\n"
            f"DERNIÈRE SESSION : {derniere_session}\n"
            f"AMÉLIORATIONS IDENTIFIÉES :\n{amelio_str}"
        )
    except Exception as e:
        return f"CRM non disponible : {e}"


def _repondre_avec_claude(
    question: str,
    historique: list[dict],
    client: anthropic.Anthropic,
) -> str:
    """Génère une réponse contextuelle via Claude Haiku (rapide et économique)."""
    crm_context = _get_crm_context()
    system_with_context = (
        f"{_BOT_SYSTEM}\n\n"
        f"═══ ÉTAT ACTUEL DU CRM ═══\n"
        f"{crm_context}"
    )

    # Garder les 6 derniers échanges pour le contexte de conversation
    messages_history = historique[-6:] if historique else []
    messages_history.append({"role": "user", "content": question})

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=600,
        system=[
            {
                "type": "text",
                "text": system_with_context,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=messages_history,
    )
    return response.content[0].text


def run_bot_cycle() -> None:
    """Cycle principal : récupérer les messages, répondre, sauvegarder l'état."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not token or not chat_id or not api_key:
        print("[BOT] Variables d'environnement manquantes — arrêt")
        sys.exit(1)

    state = _load_state()
    last_update_id = state.get("last_update_id", 0)
    historique = state.get("historique", [])

    print(f"[BOT] Vérification depuis update_id={last_update_id}")

    try:
        updates = _get_updates(token, last_update_id + 1 if last_update_id else 0)
    except Exception as e:
        print(f"[BOT] Erreur getUpdates : {e}")
        sys.exit(0)  # Ne pas faire échouer le workflow GitHub

    if not updates:
        print("[BOT] Aucun nouveau message")
        return

    client = anthropic.Anthropic(api_key=api_key)
    messages_traites = 0

    for update in updates:
        update_id = update.get("update_id", 0)
        state["last_update_id"] = max(last_update_id, update_id)

        message = update.get("message", {})
        from_chat = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "").strip()

        # Sécurité : répondre uniquement au chat d'Etienne
        if from_chat != str(chat_id):
            print(f"[BOT] Message ignoré (chat inconnu : {from_chat})")
            continue

        if not text or text.startswith("/"):
            # Commande /start ou /help
            if text == "/start":
                _send_message(token, chat_id,
                    "Bonjour Etienne ! Je suis ton Superviseur IA Fix72.\n\n"
                    "Tu peux me poser toutes tes questions sur la prospection, "
                    "l'équipe, les résultats ou les prochaines actions.\n\n"
                    "Exemples :\n"
                    "• Où en est la prospection ?\n"
                    "• Combien d'emails cette semaine ?\n"
                    "• Quel secteur fonctionne le mieux ?\n"
                    "• Que penses-tu du chef prospection ?"
                )
            continue

        print(f"[BOT] Question : {text[:100]}")

        try:
            reponse = _repondre_avec_claude(text, historique, client)

            # Mettre à jour l'historique de conversation (max 10 échanges)
            historique.append({"role": "user", "content": text})
            historique.append({"role": "assistant", "content": reponse})
            if len(historique) > 20:
                historique = historique[-20:]

            _send_message(token, chat_id, reponse)
            messages_traites += 1
            print(f"[BOT] Réponse envoyée ({len(reponse)} chars)")

        except Exception as e:
            print(f"[BOT] Erreur réponse : {e}")
            try:
                _send_message(token, chat_id,
                    f"Désolé, une erreur s'est produite : {e}\n"
                    "Réessaie dans quelques minutes.")
            except Exception:
                pass

    state["historique"] = historique
    _save_state(state)
    print(f"[BOT] {messages_traites} message(s) traité(s) — last_update_id={state['last_update_id']}")


if __name__ == "__main__":
    run_bot_cycle()
