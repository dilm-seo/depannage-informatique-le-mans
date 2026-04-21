"""
CRM — mémoire persistante des prospects contactés par Fix72.

Stocké dans agents/data/crm.json, commité après chaque session.
Permet aux agents de :
  - Ne jamais recontacter deux fois la même entreprise
  - Suivre les taux de réponse par secteur et canal
  - Programmer des relances
  - Alimenter l'auto-évaluation du Superviseur
"""

from __future__ import annotations

import json
import hashlib
from datetime import date, datetime
from pathlib import Path

_CRM_PATH = Path(__file__).parent.parent / "data" / "crm.json"


def _load() -> dict:
    if not _CRM_PATH.exists():
        return {"contacts": [], "stats": {}, "objectifs": {}, "ameliorations": [], "derniere_session": None}
    return json.loads(_CRM_PATH.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    _CRM_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _fingerprint(telephone: str = "", email: str = "") -> str:
    raw = (telephone.replace(" ", "").replace(".", "") + email.lower()).strip()
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# ─── Lecture ─────────────────────────────────────────────────────────────────

def est_deja_contacte(telephone: str = "", email: str = "") -> bool:
    """Retourne True si ce prospect a déjà été contacté."""
    if not telephone and not email:
        return False
    fp = _fingerprint(telephone, email)
    crm = _load()
    return any(c.get("fingerprint") == fp for c in crm["contacts"])


def get_stats() -> dict:
    """Retourne les statistiques complètes du CRM."""
    return _load()


def get_relances_du_jour() -> list[dict]:
    """Retourne les prospects à relancer aujourd'hui (J+7 et J+30)."""
    crm = _load()
    aujourd_hui = date.today().isoformat()
    return [c for c in crm["contacts"] if c.get("date_relance") == aujourd_hui]


def get_resume_performance() -> str:
    """Résumé lisible des performances pour le Superviseur."""
    crm = _load()
    stats = crm.get("stats", {})
    total = stats.get("total_contactes", 0)
    reponses = stats.get("reponses", 0)
    convertis = stats.get("convertis", 0)
    taux = round(reponses / total * 100, 1) if total > 0 else 0

    par_secteur = stats.get("par_secteur", {})
    meilleur = max(par_secteur.items(), key=lambda x: x[1].get("taux_reponse", 0), default=("—", {})) if par_secteur else ("—", {})

    ameliorations = crm.get("ameliorations", [])
    derniere_amelio = ameliorations[-1] if ameliorations else "Aucune encore"

    objectifs = crm.get("objectifs", {})

    return (
        f"PERFORMANCE CRM FIX72 :\n"
        f"  Total contactés : {total}\n"
        f"  Réponses : {reponses} ({taux}%)\n"
        f"  Conversions : {convertis}\n"
        f"  Meilleur secteur : {meilleur[0]}\n"
        f"  Objectif semaine : {objectifs.get('contacts_semaine', 40)} contacts\n"
        f"  Taux réponse cible : {objectifs.get('taux_reponse_cible', 8)}%\n"
        f"  Dernière amélioration : {derniere_amelio}\n"
        f"  Relances aujourd'hui : {len(get_relances_du_jour())}"
    )


# ─── Écriture ─────────────────────────────────────────────────────────────────

def ajouter_prospect(
    nom_entreprise: str,
    secteur: str,
    telephone: str = "",
    email: str = "",
    source: str = "web",
    message_envoye: str = "",
    canal: str = "email",
) -> str:
    """
    Ajoute un prospect au CRM après contact.
    Retourne 'ajouté' ou 'déjà_contacté'.
    """
    if est_deja_contacte(telephone, email):
        return f"déjà_contacté — {nom_entreprise} est déjà dans le CRM"

    crm = _load()
    aujourd_hui = date.today().isoformat()

    from datetime import timedelta
    date_relance = (date.today() + timedelta(days=7)).isoformat()

    contact = {
        "fingerprint": _fingerprint(telephone, email),
        "nom": nom_entreprise,
        "secteur": secteur,
        "telephone": telephone,
        "email": email,
        "source": source,
        "canal": canal,
        "message_envoye": message_envoye[:500],
        "date_contact": aujourd_hui,
        "date_relance": date_relance,
        "statut": "contacté",
        "notes": "",
    }
    crm["contacts"].append(contact)

    # Mise à jour stats
    stats = crm.setdefault("stats", {})
    stats["total_contactes"] = stats.get("total_contactes", 0) + 1
    stats.setdefault("par_secteur", {}).setdefault(secteur, {"contactes": 0, "reponses": 0, "taux_reponse": 0})
    stats["par_secteur"][secteur]["contactes"] += 1
    stats.setdefault("par_canal", {}).setdefault(canal, 0)
    stats["par_canal"][canal] += 1
    stats.setdefault("par_source", {}).setdefault(source, 0)
    stats["par_source"][source] += 1

    crm["derniere_session"] = datetime.now().isoformat()
    _save(crm)
    return f"ajouté — {nom_entreprise} ({secteur}) enregistré dans le CRM"


def enregistrer_reponse(telephone: str, statut: str, notes: str = "") -> str:
    """Marque un prospect comme ayant répondu (statut: répondu/converti/injoignable)."""
    crm = _load()
    fp = _fingerprint(telephone)
    for c in crm["contacts"]:
        if c.get("fingerprint") == fp or c.get("telephone", "").replace(" ", "") == telephone.replace(" ", ""):
            c["statut"] = statut
            c["notes"] = notes
            if statut in ("répondu", "converti"):
                crm["stats"]["reponses"] = crm["stats"].get("reponses", 0) + 1
                secteur = c.get("secteur", "")
                if secteur in crm["stats"].get("par_secteur", {}):
                    sect = crm["stats"]["par_secteur"][secteur]
                    sect["reponses"] = sect.get("reponses", 0) + 1
                    total = sect.get("contactes", 1)
                    sect["taux_reponse"] = round(sect["reponses"] / total * 100, 1)
            if statut == "converti":
                crm["stats"]["convertis"] = crm["stats"].get("convertis", 0) + 1
            _save(crm)
            return f"Prospect mis à jour : {c['nom']} → {statut}"
    return f"Prospect non trouvé pour le numéro {telephone}"


def enregistrer_amelioration(amelioration: str) -> str:
    """Enregistre une amélioration identifiée par le Superviseur."""
    crm = _load()
    crm.setdefault("ameliorations", []).append(f"{date.today().isoformat()} — {amelioration}")
    _save(crm)
    return f"Amélioration enregistrée : {amelioration}"


def mettre_a_jour_objectifs(contacts_semaine: int = None, taux_reponse_cible: int = None, conversions_mois: int = None) -> str:
    """Met à jour les objectifs de prospection."""
    crm = _load()
    obj = crm.setdefault("objectifs", {})
    if contacts_semaine:
        obj["contacts_semaine"] = contacts_semaine
    if taux_reponse_cible:
        obj["taux_reponse_cible"] = taux_reponse_cible
    if conversions_mois:
        obj["conversions_mois"] = conversions_mois
    _save(crm)
    return f"Objectifs mis à jour : {obj}"


# ─── Outils Anthropic ─────────────────────────────────────────────────────────

OUTIL_CRM_AJOUTER: dict = {
    "name": "crm_ajouter_prospect",
    "description": (
        "Enregistre un prospect dans le CRM après l'avoir contacté. "
        "À appeler APRÈS chaque envoi d'email ou Telegram. "
        "Vérifie automatiquement si ce prospect a déjà été contacté — "
        "si oui, retourne 'déjà_contacté' et tu passes au suivant."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "nom_entreprise": {"type": "string", "description": "Nom exact de l'entreprise"},
            "secteur": {"type": "string", "description": "Secteur d'activité"},
            "telephone": {"type": "string", "description": "Numéro de téléphone (vide si inconnu)"},
            "email": {"type": "string", "description": "Adresse email (vide si inconnue)"},
            "source": {"type": "string", "enum": ["web", "sirene", "linkedin", "relance"], "description": "Source du prospect"},
            "message_envoye": {"type": "string", "description": "Contenu du message envoyé"},
            "canal": {"type": "string", "enum": ["email", "telegram", "linkedin"], "description": "Canal utilisé"},
        },
        "required": ["nom_entreprise", "secteur"],
    },
}

OUTIL_CRM_VERIFIER: dict = {
    "name": "crm_verifier_prospect",
    "description": (
        "Vérifie si une entreprise a déjà été contactée avant d'envoyer quoi que ce soit. "
        "TOUJOURS appeler cet outil avant d'envoyer un email ou un message."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "telephone": {"type": "string", "description": "Numéro de téléphone à vérifier"},
            "email": {"type": "string", "description": "Email à vérifier"},
        },
    },
}

OUTIL_CRM_STATS: dict = {
    "name": "crm_get_stats",
    "description": "Récupère les statistiques de performance du CRM pour l'auto-évaluation.",
    "input_schema": {"type": "object", "properties": {}},
}
