"""Honeypot management module for network simulation.

Deploys and manages honeypot instances for threat detection and research.
"""
from __future__ import annotations

import json
import os
import uuid
import random
from datetime import datetime, timezone
from typing import Any
from dataclasses import dataclass, field


@dataclass
class HoneypotInstance:
    id: str
    type: str
    ip: str
    port: int
    status: str
    deployed_at: str
    interactions: int = 0
    last_interaction: str | None = None
    captured_credentials: list[dict[str, Any]] = field(default_factory=list)
    captured_files: list[dict[str, Any]] = field(default_factory=list)


class HoneypotManager:
    """Manages honeypot deployment, monitoring, and data collection."""

    HONEYPOT_TYPES = {
        "cowrie": {"port": 22, "protocol": "SSH/Telnet", "description": "SSH/Telnet honeypot"},
        "dionaea": {"port": 80, "protocol": "HTTP/Malware", "description": "Low-interaction malware honeypot"},
        "snare": {"port": 445, "protocol": "SMB", "description": "SMB honeypot"},
        "elasticpot": {"port": 9200, "protocol": "Elasticsearch", "description": "Elasticsearch honeypot"},
        "conpot": {"port": 502, "protocol": "SCADA/ICS", "description": "ICS/SCADA honeypot"},
        "glastopf": {"port": 80, "protocol": "Web", "description": "Web application honeypot"},
        "tanner": {"port": 80, "protocol": "Web", "description": "Web honeypot for Cowrie"},
    }

    def __init__(self, output_dir: str = "/tmp/quantum_simulations/honeypots"):
        self.output_dir = output_dir
        self.session_id = str(uuid.uuid4())
        self._honeypots: dict[str, HoneypotInstance] = {}
        self._all_interactions: list[dict[str, Any]] = []
        os.makedirs(self.output_dir, exist_ok=True)

    def _generate_ip(self) -> str:
        """Generate a honeypot IP address."""
        return f"10.20.0.{random.randint(2, 254)}"

    def deploy_honeypot(self, honeypot_type: str = "cowrie") -> dict[str, Any]:
        """Deploy a new honeypot instance.

        Args:
            honeypot_type: Type of honeypot to deploy (cowrie, dionaea, etc.)

        Returns:
            Honeypot deployment info.
        """
        if honeypot_type not in self.HONEYPOT_TYPES:
            raise ValueError(f"Unsupported honeypot type: {honeypot_type}")

        config = self.HONEYPOT_TYPES[honeypot_type]
        honeypot_id = f"hp-{honeypot_type}-{uuid.uuid4().hex[:8]}"
        hp = HoneypotInstance(
            id=honeypot_id,
            type=honeypot_type,
            ip=self._generate_ip(),
            port=config["port"],
            status="deployed",
            deployed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )

        self._honeypots[honeypot_id] = hp
        self._save_state()

        return {
            "id": honeypot_id,
            "type": honeypot_type,
            "ip": hp.ip,
            "port": hp.port,
            "protocol": config["protocol"],
            "description": config["description"],
            "status": hp.status,
            "deployed_at": hp.deployed_at,
        }

    def get_honeypot_stats(self) -> dict[str, Any]:
        """Return statistics about all honeypots."""
        total_interactions = sum(hp.interactions for hp in self._honeypots.values())
        total_creds = sum(len(hp.captured_credentials) for hp in self._honeypots.values())

        type_distribution = {}
        for hp in self._honeypots.values():
            type_distribution[hp.type] = type_distribution.get(hp.type, 0) + 1

        status_distribution = {}
        for hp in self._honeypots.values():
            status_distribution[hp.status] = status_distribution.get(hp.status, 0) + 1

        return {
            "total_honeypots": len(self._honeypots),
            "total_interactions": total_interactions,
            "total_credentials_captured": total_creds,
            "type_distribution": type_distribution,
            "status_distribution": status_distribution,
            "all_interactions": len(self._all_interactions),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

    def _save_state(self) -> None:
        """Save current state to file."""
        state_path = os.path.join(self.output_dir, "state.json")
        state = {
            "session_id": self.session_id,
            "honeypots": [
                {
                    "id": hp.id,
                    "type": hp.type,
                    "ip": hp.ip,
                    "port": hp.port,
                    "status": hp.status,
                    "deployed_at": hp.deployed_at,
                    "interactions": hp.interactions,
                    "last_interaction": hp.last_interaction,
                }
                for hp in self._honeypots.values()
            ],
        }
        with open(state_path, "w") as f:
            json.dump(state, f, indent=2)
