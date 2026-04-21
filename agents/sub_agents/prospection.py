"""Chef d'Équipe Prospection — développement commercial et génération de leads."""

from agents.config import CHEF_PROSPECTION_SYSTEM
from agents.sub_agents.base import ChefEquipe


class ChefEquipeProspection(ChefEquipe):
    def __init__(self) -> None:
        super().__init__(
            nom="PROSPECTION",
            system_prompt=CHEF_PROSPECTION_SYSTEM,
        )
