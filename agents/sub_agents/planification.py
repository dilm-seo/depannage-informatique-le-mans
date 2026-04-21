"""Chef d'Équipe Planification — organisation et planning journalier."""

from agents.config import CHEF_PLANIFICATION_SYSTEM
from agents.sub_agents.base import ChefEquipe


class ChefEquipePlanification(ChefEquipe):
    def __init__(self) -> None:
        super().__init__(
            nom="PLANIFICATION",
            system_prompt=CHEF_PLANIFICATION_SYSTEM,
        )
