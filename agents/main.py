#!/usr/bin/env python3
"""
Système d'Agents IA — Sarthe Fix72
Point d'entrée principal pour la gestion journalière.

Usage :
    python -m agents.main
    python -m agents.main --contexte "Interventions : 2 réparations PC, 1 virus à nettoyer"
    python -m agents.main --fichier contexte.txt
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from agents.config import BUSINESS
from agents.supervisor import Superviseur
from agents.utils import logger

# Chargement des variables d'environnement
load_dotenv(Path(__file__).parent / ".env")
load_dotenv()  # fallback sur le .env racine

# ─── Contexte par défaut ──────────────────────────────────────────────────────
CONTEXTE_DEFAUT = """Journée type sans informations spécifiques fournies.

SITUATION GÉNÉRALE :
- Entreprise opérationnelle, disponible pour de nouvelles missions
- Agenda partiellement libre, en attente d'interventions
- Objectif : développer le portefeuille clients et optimiser la rentabilité

TÂCHES RÉCURRENTES :
- Répondre aux demandes entrantes (appels, emails, réseaux sociaux)
- Assurer la visibilité sur Google My Business et les réseaux sociaux
- Effectuer le suivi des devis envoyés non-signés
- Prospecter de nouveaux clients (particuliers et professionnels)
"""


# ─── Sauvegarde du rapport ────────────────────────────────────────────────────
def sauvegarder_rapport(rapport: str) -> Path:
    """Sauvegarde le rapport dans le dossier rapports/ avec horodatage."""
    rapports_dir = Path(__file__).parent / "rapports"
    rapports_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = rapports_dir / f"rapport_{timestamp}.md"

    filename.write_text(rapport, encoding="utf-8")
    return filename


# ─── Saisie interactive du contexte ──────────────────────────────────────────
def saisir_contexte_interactif() -> str:
    """Guide l'utilisateur pour saisir le contexte de sa journée."""
    logger.section("SAISIE DU CONTEXTE JOURNALIER")

    print("Décrivez le contexte de votre journée (appuyez sur Entrée 2 fois pour valider) :")
    print("Exemples : interventions prévues, urgences, objectifs commerciaux, zone de travail...\n")

    lignes: list[str] = []
    vide_count = 0
    try:
        while True:
            ligne = input()
            if ligne == "":
                vide_count += 1
                if vide_count >= 2:
                    break
            else:
                vide_count = 0
                lignes.append(ligne)
    except (EOFError, KeyboardInterrupt):
        pass

    contexte = "\n".join(lignes).strip()
    return contexte if contexte else CONTEXTE_DEFAUT


# ─── Parsing des arguments ────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"Système d'Agents IA — {BUSINESS['name']}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  python -m agents.main
  python -m agents.main --contexte "3 interventions PC, prospection PME"
  python -m agents.main --fichier mon_contexte.txt
  python -m agents.main --demo
        """,
    )
    parser.add_argument(
        "--contexte", "-c",
        type=str,
        help="Contexte de la journée (texte direct)",
    )
    parser.add_argument(
        "--fichier", "-f",
        type=Path,
        help="Fichier texte contenant le contexte de la journée",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Utilise un contexte de démonstration réaliste",
    )
    parser.add_argument(
        "--sortie", "-o",
        type=Path,
        help="Chemin personnalisé pour sauvegarder le rapport (optionnel)",
    )
    return parser.parse_args()


# ─── Contexte de démonstration ────────────────────────────────────────────────
CONTEXTE_DEMO = """Journée chargée en perspectives :

INTERVENTIONS PLANIFIÉES :
- 09h00 : Réparation PC portable chez Mme Leblanc (Le Mans centre) — écran fissuré
- 11h00 : Suppression virus + nettoyage PC chez M. Dupont (La Flèche) — prise en charge à distance possible
- 14h00 : Installation et configuration NAS pour la boulangerie Artisan Saveur (Le Mans nord)

URGENCES / SIGNALEMENTS :
- Email reçu hier soir : M. Moreau (retraité, Sablé-sur-Sarthe) a perdu toutes ses photos famille suite à une panne disque dur → priorité récupération données
- Un artisan plombier intéressé par un contrat de maintenance mensuel — rappel à faire

SITUATION COMMERCIALE :
- 2 devis envoyés la semaine dernière sans réponse (installation bureau domicile + formation Word/Excel)
- Avis Google : 4.7 étoiles (23 avis) — pas de nouveaux avis depuis 3 semaines
- Page Facebook : dernière publication il y a 10 jours

OBJECTIFS DU MOIS :
- Atteindre 5 contrats de maintenance récurrents (actuellement 2)
- Développer la clientèle TPE/PME dans la zone Le Mans nord
- Améliorer la visibilité sur Google My Business
"""


# ─── Point d'entrée principal ─────────────────────────────────────────────────
def main() -> None:
    args = parse_args()

    # Vérification clé API
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.error("Variable d'environnement ANTHROPIC_API_KEY non définie.")
        logger.error("Copiez agents/.env.example vers agents/.env et renseignez votre clé API.")
        sys.exit(1)

    # ─── Bannière de démarrage ────────────────────────────────────────────────
    logger.section(f"SYSTÈME D'AGENTS IA — {BUSINESS['name']}")
    logger.info(f"Site : {BUSINESS['website']}  |  Zone : {BUSINESS['zone']}")
    logger.info(f"Superviseur : claude-opus-4-7  |  Sous-agents : claude-haiku-4-5")
    print()

    # ─── Détermination du contexte ────────────────────────────────────────────
    if args.demo:
        logger.info("Mode démonstration activé")
        contexte = CONTEXTE_DEMO
    elif args.fichier:
        if not args.fichier.exists():
            logger.error(f"Fichier introuvable : {args.fichier}")
            sys.exit(1)
        contexte = args.fichier.read_text(encoding="utf-8").strip()
        logger.info(f"Contexte chargé depuis : {args.fichier}")
    elif args.contexte:
        contexte = args.contexte
        logger.info("Contexte fourni en ligne de commande")
    else:
        contexte = saisir_contexte_interactif()

    if not contexte.strip():
        logger.warn("Aucun contexte fourni — utilisation du contexte par défaut")
        contexte = CONTEXTE_DEFAUT

    logger.section("LANCEMENT DU SUPERVISEUR")

    # ─── Exécution du superviseur ─────────────────────────────────────────────
    superviseur = Superviseur()

    try:
        rapport = superviseur.run(contexte)
    except anthropic.AuthenticationError:
        logger.error("Clé API invalide. Vérifiez votre ANTHROPIC_API_KEY.")
        sys.exit(1)
    except anthropic.RateLimitError:
        logger.error("Limite de taux API atteinte. Réessayez dans quelques instants.")
        sys.exit(1)
    except anthropic.APIError as e:
        logger.error(f"Erreur API Anthropic : {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warn("Interruption utilisateur — arrêt du système")
        sys.exit(0)

    # ─── Sauvegarde du rapport ────────────────────────────────────────────────
    logger.section("RAPPORT JOURNALIER")

    if args.sortie:
        args.sortie.parent.mkdir(parents=True, exist_ok=True)
        args.sortie.write_text(rapport, encoding="utf-8")
        chemin_rapport = args.sortie
    else:
        chemin_rapport = sauvegarder_rapport(rapport)

    # Affichage du rapport dans le terminal
    print(rapport)
    print()
    logger.success(f"Rapport sauvegardé : {chemin_rapport}")

    logger.section("JOURNÉE TRAITÉE")


# Nécessaire pour l'import du module anthropic dans les sous-agents
import anthropic  # noqa: E402 — import tardif pour éviter l'import avant load_dotenv

if __name__ == "__main__":
    main()
