"""Purple team orchestration module.

Coordinates red team attacks with blue team defenses in adversarial exercises.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Any

from .red_team_sim import RedTeamSimulator
from .blue_team_sim import BlueTeamSimulator


class PurpleTeamOrchestrator:
    """Orchestrates purple team exercises combining red and blue team simulations."""

    EXERCISE_CONFIGS = {
        "full_scope": {
            "rounds": 3,
            "scope": "enterprise",
            "duration_hours": 72,
        },
        "targeted": {
            "rounds": 1,
            "scope": "segment",
            "duration_hours": 8,
        },
        "continuous": {
            "rounds": 10,
            "scope": "enterprise",
            "duration_hours": 168,
        },
    }

    def __init__(self, output_dir: str = "/tmp/quantum_simulations/purple"):
        self.output_dir = output_dir
        self.simulation_id = str(uuid.uuid4())
        self.red_team = RedTeamSimulator(os.path.join(output_dir, "red"))
        self.blue_team = BlueTeamSimulator(os.path.join(output_dir, "blue"))
        os.makedirs(self.output_dir, exist_ok=True)

    def _log(self, event_type: str, data: dict[str, Any]) -> None:
        """Log orchestration event."""
        log_path = os.path.join(self.output_dir, "orchestration.log.jsonl")
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": event_type,
            "sim_id": self.simulation_id,
            "data": data,
        }
        with open(log_path, "a") as f:
            f.write(json.dumps(event) + "\n")

    def run_adversarial_exercise(
        self, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Run a full adversarial exercise based on config."""
        self._log("exercise_start", {"config": config})

        rounds = config.get("rounds", 3)
        target_profile = config.get("target_profile", {"name": "default_target"})
        network_topology = config.get("network_topology", {"max_hops": 3})
        data_profile = config.get("data_profile", {"sensitive_data_size_mb": 10})

        round_results = []
        for round_num in range(1, rounds + 1):
            self._log("round_start", {"round": round_num})

            attack = self.red_team.simulate_credential_harvesting(target_profile)
            attack["round"] = round_num

            defense_config = {
                "type": "data_breach",
                "severity": "critical" if round_num == rounds else "high",
            }
            defense = self.blue_team.simulate_incident_response(defense_config)
            defense["round"] = round_num

            round_results.append({
                "round": round_num,
                "attack": attack,
                "defense": defense,
                "detection_time_seconds": 120 * round_num,
                "response_time_seconds": 300 * round_num,
                "lessons_learned": f"Round {round_num}: detection improved by 15%",
            })

            self._log("round_complete", {"round": round_num})

        summary = {
            "total_rounds": rounds,
            "total_attacks": rounds,
            "total_defenses": rounds,
            "detection_improvement": True,
            "avg_detection_time": sum(r["detection_time_seconds"] for r in round_results) / rounds,
            "avg_response_time": sum(r["response_time_seconds"] for r in round_results) / rounds,
        }

        result = {
            "simulation_type": "adversarial_exercise",
            "simulation_id": self.simulation_id,
            "exercsie_config": config,
            "rounds": round_results,
            "summary": summary,
            "target_profile": target_profile,
            "network_topology": network_topology,
            "data_profile": data_profile,
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        self._log("exercise_complete", result)
        return result

    def get_exercise_summary(self) -> dict[str, Any]:
        """Get a summary of all exercises run in this session."""
        return {
            "simulation_id": self.simulation_id,
            "total_exercises": len(getattr(self, "_exercises", [])),
            "red_team": "active",
            "blue_team": "active",
            "available_configs": list(self.EXERCISE_CONFIGS.keys()),
        }
