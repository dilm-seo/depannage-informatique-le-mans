"""Chef d'Équipe Rapport — compilation du compte-rendu journalier final."""

from datetime import date

import anthropic

from agents.config import CHEF_MODEL, CHEF_RAPPORT_SYSTEM, BUSINESS
from agents.sub_agents.base import ChefEquipe, RapportEquipe
from agents.utils import logger

# Noms français pour l'horodatage du rapport
_JOURS_FR  = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
_MOIS_FR   = ["janvier", "février", "mars", "avril", "mai", "juin",
               "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


class ChefEquipeRapport(ChefEquipe):
    """
    Chef d'Équipe Rapport — reçoit les 3 rapports validés + la synthèse du
    Superviseur, puis génère le compte-rendu journalier final en Markdown.

    Contrairement aux autres chefs, il est appelé directement par le Superviseur
    via `compiler_rapport_final` et reçoit les données compilées.
    """

    def __init__(self) -> None:
        super().__init__(
            nom="RAPPORT",
            system_prompt=CHEF_RAPPORT_SYSTEM,
        )

    def compiler(
        self,
        client: anthropic.Anthropic,
        rapport_planification: str,
        rapport_prospection: str,
        rapport_strategie: str,
        contexte_general: str,
        synthese_superviseur: str = "",
    ) -> str:
        """
        Compile les rapports des trois chefs en un compte-rendu final.

        Returns:
            Compte-rendu journalier complet en Markdown
        """
        logger.chef("RAPPORT", "Compilation du compte-rendu final…")

        today = date.today()
        date_fr = f"{_JOURS_FR[today.weekday()]} {today.day} {_MOIS_FR[today.month - 1]} {today.year}"

        synthese_block = ""
        if synthese_superviseur:
            synthese_block = f"\n\nSYNTHÈSE DU SUPERVISEUR :\n{synthese_superviseur}"

        # Directive construite dynamiquement avec les 3 rapports
        directive = (
            f"Compile les rapports suivants en un compte-rendu journalier pour le {date_fr}."
            f"{synthese_block}"
        )

        contexte_compile = (
            f"CONTEXTE GÉNÉRAL DU JOUR :\n{contexte_general}\n\n"
            f"{'═' * 60}\n"
            f"RAPPORT CHEF PLANIFICATION :\n{rapport_planification}\n\n"
            f"{'═' * 60}\n"
            f"RAPPORT CHEF PROSPECTION :\n{rapport_prospection}\n\n"
            f"{'═' * 60}\n"
            f"RAPPORT CHEF STRATÉGIE :\n{rapport_strategie}\n"
        )

        result: RapportEquipe = self.run(
            client=client,
            directive=directive,
            contexte=contexte_compile,
        )

        logger.chef("RAPPORT", "Compte-rendu généré avec succès")
        return result.rapport
