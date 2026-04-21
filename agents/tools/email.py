"""
Outil Email — envoi d'emails aux prospects via Gmail SMTP.
Utilise le mot de passe d'application Google (pas le mot de passe principal).

Paramètres dans .env :
  GMAIL_EMAIL        = etienne06080608@gmail.com
  GMAIL_APP_PASSWORD = xxxx xxxx xxxx xxxx  (mot de passe d'application Google)

Si le port SMTP est bloqué (hébergeur cloud), l'email est envoyé
automatiquement en fallback sur Telegram.
"""

from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587


def _get_credentials() -> tuple[str, str]:
    email = os.environ.get("GMAIL_EMAIL", "")
    password = os.environ.get("GMAIL_APP_PASSWORD", "")
    return email, password


def envoyer_email_prospect(
    destinataire_email: str,
    destinataire_nom: str,
    sujet: str,
    corps: str,
) -> str:
    """
    Envoie un email de prospection personnalisé à une entreprise.

    Args:
        destinataire_email: Adresse email du prospect
        destinataire_nom:   Nom de l'entreprise ou du contact
        sujet:              Objet de l'email
        corps:              Corps de l'email (texte)

    Returns:
        Message de confirmation ou d'erreur
    """
    expediteur, password = _get_credentials()
    if not expediteur or not password:
        return "[ERREUR] ICLOUD_EMAIL ou ICLOUD_APP_PASSWORD manquant dans .env"

    # Signature automatique Fix72
    corps_complet = (
        f"{corps}\n\n"
        f"---\n"
        f"Etienne Aubry — Fix72\n"
        f"Dépannage informatique Le Mans & Sarthe\n"
        f"📱 06 64 31 34 74 | 🌐 fix72.com\n"
        f"Diagnostic gratuit · Intervention sous 2h · 4,9/5 sur 850+ clients"
    )

    msg = MIMEMultipart("alternative")
    msg["From"] = f"Etienne Aubry — Fix72 <{expediteur}>"
    msg["To"] = f"{destinataire_nom} <{destinataire_email}>"
    msg["Subject"] = sujet
    msg["Reply-To"] = expediteur
    msg.attach(MIMEText(corps_complet, "plain", "utf-8"))

    try:
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(expediteur, password)
            server.send_message(msg)
        return f"✅ Email envoyé avec succès à {destinataire_nom} <{destinataire_email}>"
    except smtplib.SMTPAuthenticationError:
        return "[ERREUR] Authentification iCloud échouée — vérifie le mot de passe d'application."
    except Exception:
        # Fallback : envoyer le brouillon sur Telegram si SMTP bloqué
        return _fallback_telegram(destinataire_nom, destinataire_email, sujet, corps_complet)


def _fallback_telegram(nom: str, email: str, sujet: str, corps: str) -> str:
    """SMTP indisponible — envoie le brouillon d'email sur Telegram."""
    from agents.tools.telegram import envoyer_message
    texte = (
        f"📧 *Email à envoyer — SMTP indisponible*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*À :* {nom}\n"
        f"*Adresse :* `{email}`\n"
        f"*Objet :* {sujet}\n\n"
        f"*Corps du message :*\n"
        f"```\n{corps[:800]}\n```\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"_Copie et envoie depuis ton client email._"
    )
    result = envoyer_message(texte)
    return f"SMTP bloqué — brouillon envoyé sur Telegram pour {nom} <{email}>"


def envoyer_email_interne(sujet: str, corps: str) -> str:
    """Envoie un email à Etienne lui-même (notifications internes)."""
    expediteur, _ = _get_credentials()
    return envoyer_email_prospect(
        destinataire_email=expediteur,
        destinataire_nom="Etienne Fix72",
        sujet=sujet,
        corps=corps,
    )


# ─── Définition de l'outil pour les agents ───────────────────────────────────

OUTIL_EMAIL: dict = {
    "name": "envoyer_email_prospect",
    "description": (
        "Envoie un email de prospection personnalisé directement à une entreprise. "
        "Utilise quand tu as trouvé l'adresse email d'un prospect qualifié. "
        "La signature Fix72 est ajoutée automatiquement. "
        "Privilégie Telegram quand tu n'as que le téléphone."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "destinataire_email": {
                "type": "string",
                "description": "Adresse email du prospect (ex: contact@plomberie-martin.fr)",
            },
            "destinataire_nom": {
                "type": "string",
                "description": "Nom de l'entreprise ou du contact",
            },
            "sujet": {
                "type": "string",
                "description": (
                    "Objet de l'email — accrocheur et personnalisé. "
                    "Ex: 'Maintenance informatique pour votre cabinet — Fix72 Le Mans'"
                ),
            },
            "corps": {
                "type": "string",
                "description": (
                    "Corps de l'email — personnalisé selon le secteur du prospect, "
                    "court (5-8 lignes max), avec un bénéfice concret et un appel à l'action. "
                    "La signature Fix72 est ajoutée automatiquement."
                ),
            },
        },
        "required": ["destinataire_email", "destinataire_nom", "sujet", "corps"],
    },
}
