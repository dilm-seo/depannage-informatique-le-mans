"""
Outil Telegram — envoie des notifications à Etienne (Fix72) via son bot.

Les agents utilisent cet outil pour transmettre :
  • Des messages prêts à envoyer à un prospect (avec son numéro)
  • Des alertes urgentes (relance, opportunité)
  • Le rapport journalier final
"""

from __future__ import annotations

import os
import urllib.request
import urllib.parse
import json


def _get_credentials() -> tuple[str, str]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    return token, chat_id


def envoyer_message(texte: str, parse_mode: str = "Markdown") -> str:
    """Envoie un message texte à Etienne via Telegram."""
    token, chat_id = _get_credentials()
    if not token or not chat_id:
        return "[ERREUR] TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID manquant dans .env"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": texte,
        "parse_mode": parse_mode,
    }).encode()

    try:
        req = urllib.request.Request(url, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                return "Message Telegram envoyé avec succès."
            return f"[ERREUR Telegram] {result}"
    except Exception as e:
        return f"[ERREUR] Envoi Telegram échoué : {e}"


def envoyer_prospect(
    nom_entreprise: str,
    secteur: str,
    telephone: str,
    message_a_envoyer: str,
    priorite: str = "normale",
) -> str:
    """
    Envoie à Etienne un prospect qualifié avec le message prêt à copier-coller.
    """
    emoji_priorite = {"haute": "🔴", "normale": "🟡", "basse": "🟢"}.get(priorite, "🟡")

    texte = (
        f"{emoji_priorite} *Nouveau prospect Fix72*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏢 *{nom_entreprise}* ({secteur})\n"
        f"📱 `{telephone}`\n\n"
        f"💬 *Message à envoyer :*\n"
        f"```\n{message_a_envoyer}\n```\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_Copie le message et envoie-le au numéro ci-dessus._"
    )
    return envoyer_message(texte)


def envoyer_rapport_final(rapport_markdown: str) -> str:
    """Envoie le résumé exécutif du rapport journalier à Etienne."""
    # Extraire juste le résumé exécutif (les 30 premières lignes)
    lignes = rapport_markdown.strip().splitlines()
    extrait = "\n".join(lignes[:30])
    if len(lignes) > 30:
        extrait += "\n\n_[Rapport complet sauvegardé localement]_"

    texte = f"📊 *Rapport Fix72 — résumé*\n\n{extrait}"
    return envoyer_message(texte)


# ─── Définition de l'outil pour les agents ───────────────────────────────────

OUTIL_TELEGRAM: dict = {
    "name": "envoyer_prospect_telegram",
    "description": (
        "Envoie à Etienne (Fix72) via Telegram un prospect qualifié avec le message "
        "prêt à copier-coller. Etienne recevra le nom de l'entreprise, le numéro de "
        "téléphone et le SMS/message rédigé. Il n'aura qu'à copier et envoyer. "
        "Utilise cet outil pour chaque prospect trouvé et qualifié."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "nom_entreprise": {
                "type": "string",
                "description": "Nom de l'entreprise ou du contact prospect",
            },
            "secteur": {
                "type": "string",
                "description": "Secteur d'activité (ex: plombier, cabinet médical, restaurant)",
            },
            "telephone": {
                "type": "string",
                "description": "Numéro de téléphone du prospect (trouvé sur le web)",
            },
            "message_a_envoyer": {
                "type": "string",
                "description": (
                    "Le message SMS ou script court personnalisé, prêt à copier-coller. "
                    "Doit mentionner Fix72, Etienne, et un bénéfice concret. "
                    "Maximum 160 caractères pour un SMS."
                ),
            },
            "priorite": {
                "type": "string",
                "enum": ["haute", "normale", "basse"],
                "description": "Niveau de priorité du prospect",
                "default": "normale",
            },
        },
        "required": ["nom_entreprise", "secteur", "telephone", "message_a_envoyer"],
    },
}
