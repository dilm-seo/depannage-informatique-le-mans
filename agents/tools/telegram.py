"""
Outil Telegram — notifications à Etienne (Fix72).

Telegram sert UNIQUEMENT à :
  • Le résumé du soir (ce que l'équipe a fait, les chiffres clés)
  • Les alertes importantes (prospect qui répond, opportunité urgente)

Les agents n'envoient PAS un message par prospect — ils compilent un résumé.
"""

from __future__ import annotations

import os
import urllib.request
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

    # Découper si trop long (limite Telegram = 4096 chars)
    chunks = [texte[i:i+4000] for i in range(0, len(texte), 4000)]
    for chunk in chunks:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = json.dumps({
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": parse_mode,
        }).encode()
        try:
            req = urllib.request.Request(url, data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
                if not result.get("ok"):
                    return f"[ERREUR Telegram] {result}"
        except Exception as e:
            return f"[ERREUR] Envoi Telegram échoué : {e}"
    return "Message Telegram envoyé avec succès."


def envoyer_resume_session(
    emails_envoyes: int,
    secteurs: list[str],
    nouvelles_entreprises_sirene: int,
    relances: int,
    total_crm: int,
    taux_reponse: float,
    amelioration_identifiee: str,
    alerte: str = "",
) -> str:
    """
    Envoie le résumé de fin de session à Etienne.
    Format concis, chiffres clés uniquement.
    """
    from datetime import date
    jours_fr = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
    today = date.today()
    jour = jours_fr[today.weekday()]

    secteurs_str = ", ".join(secteurs) if secteurs else "—"
    alerte_block = f"\n\n⚠️ *ALERTE :* {alerte}" if alerte else ""

    texte = (
        f"📊 *Fix72 — Résumé {jour} {today.day}/{today.month}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📧 Emails envoyés : *{emails_envoyes}*\n"
        f"🆕 Nouvelles entreprises SIRENE : *{nouvelles_entreprises_sirene}*\n"
        f"🔁 Relances : *{relances}*\n"
        f"📋 Total CRM : *{total_crm}* contacts\n"
        f"📈 Taux de réponse : *{taux_reponse}%*\n"
        f"🎯 Secteurs : {secteurs_str}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *Amélioration identifiée :*\n_{amelioration_identifiee}_"
        f"{alerte_block}"
    )
    return envoyer_message(texte)


def envoyer_alerte(message: str) -> str:
    """Alerte importante — prospect qui répond, urgence, etc."""
    texte = f"🚨 *ALERTE Fix72*\n\n{message}"
    return envoyer_message(texte)


def envoyer_rapport_final(rapport_markdown: str) -> str:
    """Envoie uniquement le résumé exécutif du rapport (pas tout le contenu)."""
    lignes = rapport_markdown.strip().splitlines()
    # Chercher la section résumé exécutif
    resume = []
    in_resume = False
    for ligne in lignes:
        if "Résumé Exécutif" in ligne or "résumé exécutif" in ligne.lower():
            in_resume = True
            continue
        if in_resume and ligne.startswith("## "):
            break
        if in_resume and ligne.strip():
            resume.append(ligne)

    extrait = "\n".join(resume[:10]) if resume else "\n".join(lignes[:15])
    texte = f"📋 *Fix72 — Résumé exécutif*\n\n{extrait}"
    return envoyer_message(texte)


# ─── Outils pour les agents ───────────────────────────────────────────────────

OUTIL_TELEGRAM_RESUME: dict = {
    "name": "envoyer_resume_telegram",
    "description": (
        "Envoie le résumé de fin de session à Etienne sur Telegram. "
        "À appeler UNE SEULE FOIS à la fin, avec les chiffres consolidés. "
        "NE PAS utiliser pour chaque prospect — uniquement le bilan final."
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
            "alerte": {"type": "string", "description": "Alerte importante si prospect a répondu ou urgence (vide sinon)"},
        },
        "required": ["emails_envoyes", "secteurs", "nouvelles_entreprises_sirene", "relances", "total_crm", "taux_reponse", "amelioration_identifiee"],
    },
}

OUTIL_TELEGRAM_ALERTE: dict = {
    "name": "envoyer_alerte_telegram",
    "description": (
        "Envoie une alerte importante à Etienne. "
        "Utiliser UNIQUEMENT pour : prospect qui a répondu, opportunité urgente, "
        "problème critique détecté. PAS pour chaque action ordinaire."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Message d'alerte concis et actionnable"},
        },
        "required": ["message"],
    },
}
