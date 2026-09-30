"""quantum.sim — red/blue/purple team simulation + network emulation.

Ported from Quantum C2 `modules/simulation_sandbox` and
`modules/network_simulation` (Tier-1 modules, approved for app
integration). Pure-stdlib simulation engines:

- red_team_sim / blue_team_sim / purple_team_orchestrator
- advanced_red_team / advanced_blue_team / advanced_purple_team
- autonomous_triggers (detection-response simulation)
- attack_scenarios (scenario library)
- network_emulator / traffic_generator / pcap_replay / honeypot_manager

These are deterministic simulations of adversary + defender behavior
for training and playbooks — not live engagement code.
"""
from .advanced_blue_team import AdvancedBlueTeamSimulator
from .advanced_purple_team import AdvancedPurpleTeamOrchestrator
from .advanced_red_team import AdvancedRedTeamSimulator
from .attack_scenarios import AttackScenarioLibrary
from .autonomous_triggers import AutonomousDefenseTriggers
from .blue_team_sim import BlueTeamSimulator
from .honeypot_manager import HoneypotManager
from .network_emulator import NetworkEmulator
from .pcap_replay import PCAPReplayEngine
from .purple_team_orchestrator import PurpleTeamOrchestrator
from .red_team_sim import RedTeamSimulator
from .traffic_generator import TrafficGenerator

__all__ = [
    "AdvancedBlueTeamSimulator",
    "AdvancedPurpleTeamOrchestrator",
    "AdvancedRedTeamSimulator",
    "AttackScenarioLibrary",
    "AutonomousDefenseTriggers",
    "BlueTeamSimulator",
    "HoneypotManager",
    "NetworkEmulator",
    "PCAPReplayEngine",
    "PurpleTeamOrchestrator",
    "RedTeamSimulator",
    "TrafficGenerator",
]
