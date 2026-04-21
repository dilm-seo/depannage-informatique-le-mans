"""Chef d'Équipe Prospection — développement commercial avec recherche web réelle."""

from agents.config import CHEF_PROSPECTION_SYSTEM
from agents.sub_agents.base import ChefEquipe
from agents.tools.web_search import OUTILS_PROSPECTION


class ChefEquipeProspection(ChefEquipe):
    # Les workers recrutés par ce chef ont accès à la recherche web DuckDuckGo
    worker_tools = OUTILS_PROSPECTION

    def __init__(self) -> None:
        super().__init__(
            nom="PROSPECTION",
            system_prompt=CHEF_PROSPECTION_SYSTEM,
        )
