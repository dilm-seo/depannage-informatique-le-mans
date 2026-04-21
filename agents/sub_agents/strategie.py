"""Chef d'Équipe Stratégie — analyse stratégique et recommandations business."""

from agents.config import CHEF_STRATEGIE_SYSTEM
from agents.sub_agents.base import ChefEquipe


class ChefEquipeStrategie(ChefEquipe):
    def __init__(self) -> None:
        super().__init__(
            nom="STRATÉGIE",
            system_prompt=CHEF_STRATEGIE_SYSTEM,
        )
