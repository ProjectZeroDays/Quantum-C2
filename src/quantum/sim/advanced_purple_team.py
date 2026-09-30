"""Advanced purple team simulation module.

Provides advanced purple team orchestration capabilities.
Re-exports AdvancedBlueTeamSimulator for compatibility.
"""
from __future__ import annotations

from .advanced_blue_team import AdvancedBlueTeamSimulator

__all__ = ["AdvancedBlueTeamSimulator"]


class AdvancedPurpleTeamOrchestrator:
    """Advanced purple-team run: advanced red + advanced blue simulation
    chained into one timeline (training helper, no live traffic)."""

    def __init__(self, scenario_name: str = "advanced-purple-drill"):
        from .advanced_red_team import AdvancedRedTeamSimulator
        self.red = AdvancedRedTeamSimulator()
        self.blue = AdvancedBlueTeamSimulator()
        self.scenario_name = scenario_name

    def run(self) -> dict:
        red = getattr(self.red, "run_simulation", None)
        blue = getattr(self.blue, "run_simulation", None)
        return {
            "scenario": self.scenario_name,
            "red": red() if callable(red) else {},
            "blue": blue() if callable(blue) else {},
        }
