"""Traffic generation module for network simulation.

Generates synthetic network traffic for both normal and malicious patterns.
"""
from __future__ import annotations

import json
import os
import random
import uuid
from datetime import datetime
from typing import Any
from dataclasses import dataclass, field


@dataclass
class FlowRecord:
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    bytes_transferred: int
    duration_seconds: float
    timestamp: str
    flow_type: str = "normal"
    tags: list[str] = field(default_factory=list)


class TrafficGenerator:
    """Generates synthetic network traffic for simulation and testing."""

    NORMAL_ACTIONS = ["web_browsing", "file_transfer", "email", "video_stream", "dns_lookup"]
    MALICIOUS_ACTIONS = ["c2_beacon", "port_scan", "credential_stuffing", "data_exfil", "lateral_movement"]

    INTERNAL_SUBNETS = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
    EXTERNAL_IPS = ["8.8.8.8", "1.1.1.1", "140.82.112.3", "52.112.82.3"]

    PORTS_BY_PROTOCOL = {
        "http": 80, "https": 443, "ssh": 22, "rdp": 3389,
        "dns": 53, "smtp": 25, "ftp": 21, "smb": 445,
        "mysql": 3306, "postgres": 5432, "redis": 6379, "mongodb": 27017,
    }

    def __init__(self, output_dir: str = "/tmp/quantum_simulations/traffic"):
        self.output_dir = output_dir
        self.session_id = str(uuid.uuid4())
        self._flows: list[FlowRecord] = []
        self._stats = {
            "total_flows": 0,
            "malicious_flows": 0,
            "normal_flows": 0,
            "bytes_transferred": 0,
            "by_protocol": {},
            "by_action": {},
        }
        os.makedirs(self.output_dir, exist_ok=True)

    def _random_ip(self, from_internal: bool = True) -> str:
        """Generate a random IP address."""
        if from_internal:
            return f"192.168.{random.randint(1, 254)}.{random.randint(2, 254)}"
        return f"203.0.113.{random.randint(1, 254)}"

    def _random_port(self) -> int:
        """Generate a random port number."""
        return random.randint(1024, 65535)

    def _generate_normal_flow(self, action: str = "web_browsing") -> FlowRecord:
        """Generate a single normal traffic flow."""
        dst_ip = random.choice(self.EXTERNAL_IPS) if action == "web_browsing" else self._random_ip(from_internal=False)
        dst_port = self.PORTS_BY_PROTOCOL.get(action, random.choice([80, 443, 53, 25]))

        flow = FlowRecord(
            src_ip=self._random_ip(),
            dst_ip=dst_ip,
            src_port=self._random_port(),
            dst_port=dst_port,
            protocol="TCP" if dst_port not in [53] else "UDP",
            bytes_transferred=random.randint(500, 50_000_000),
            duration_seconds=round(random.uniform(0.5, 60.0), 2),
            timestamp=datetime.utcnow().isoformat() + "Z",
            flow_type="normal",
            tags=[action],
        )
        self._flows.append(flow)
        return flow

    def _generate_malicious_flow(self, attack_type: str = "c2_beacon") -> FlowRecord:
        """Generate a single malicious traffic flow."""
        src_ip = self._random_ip(from_internal=True)
        dst_ip = f"203.0.113.{random.randint(1, 254)}"

        if attack_type == "c2_beacon":
            dst_port = 443
            protocol = "TCP"
            bytes_val = random.randint(100, 500)
            duration = 0.2
            tags = ["c2", "beacon", "tls"]
        elif attack_type == "port_scan":
            dst_port = random.randint(1, 65535)
            protocol = "TCP"
            bytes_val = 64
            duration = random.uniform(0.01, 0.1)
            tags = ["scan", "recon", "tcp_scan"]
        elif attack_type == "credential_stuffing":
            dst_port = 443
            protocol = "TCP"
            bytes_val = random.randint(500, 2000)
            duration = 0.3
            tags = ["attack", "brute_force", "auth"]
        elif attack_type == "data_exfil":
            dst_port = 80
            protocol = "TCP"
            bytes_val = random.randint(1_000_000, 50_000_000)
            duration = random.uniform(5, 60)
            tags = ["exfil", "data_loss", "large_transfer"]
        else:
            dst_port = 443
            protocol = "TCP"
            bytes_val = 100
            duration = 0.1
            tags = ["attack", "unknown"]

        flow = FlowRecord(
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=self._random_port(),
            dst_port=dst_port,
            protocol=protocol,
            bytes_transferred=bytes_val,
            duration_seconds=duration,
            timestamp=datetime.utcnow().isoformat() + "Z",
            flow_type="malicious",
            tags=tags,
        )
        self._flows.append(flow)
        return flow

    def generate_normal_traffic(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate normal network traffic flows.

        Args:
            count: Number of normal flows to generate.

        Returns:
            List of flow dictionaries.
        """
        flows = []
        for _ in range(count):
            action = random.choice(self.NORMAL_ACTIONS)
            flow = self._generate_normal_flow(action)

            self._stats["normal_flows"] += 1
            self._stats["total_flows"] += 1
            self._stats["bytes_transferred"] += flow.bytes_transferred
            self._stats["by_protocol"][flow.protocol] = self._stats["by_protocol"].get(flow.protocol, 0) + 1
            self._stats["by_action"][action] = self._stats["by_action"].get(action, 0) + 1

            flows.append({
                "src_ip": flow.src_ip,
                "dst_ip": flow.dst_ip,
                "src_port": flow.src_port,
                "dst_port": flow.dst_port,
                "protocol": flow.protocol,
                "bytes": flow.bytes_transferred,
                "duration": flow.duration_seconds,
                "timestamp": flow.timestamp,
                "type": flow.flow_type,
                "tags": flow.tags,
            })

        self._save_flows(flows, "normal")
        return flows

    def generate_malicious_traffic(self, attack_type: str = "c2_beacon", count: int = 50) -> list[dict[str, Any]]:
        """Generate malicious network traffic flows.

        Args:
            attack_type: Type of malicious traffic to generate.
            count: Number of malicious flows to generate.

        Returns:
            List of flow dictionaries.
        """
        flows = []
        for _ in range(count):
            flow = self._generate_malicious_flow(attack_type)

            self._stats["malicious_flows"] += 1
            self._stats["total_flows"] += 1
            self._stats["bytes_transferred"] += flow.bytes_transferred
            self._stats["by_protocol"][flow.protocol] = self._stats["by_protocol"].get(flow.protocol, 0) + 1
            self._stats["by_action"][attack_type] = self._stats["by_action"].get(attack_type, 0) + 1

            flows.append({
                "src_ip": flow.src_ip,
                "dst_ip": flow.dst_ip,
                "src_port": flow.src_port,
                "dst_port": flow.dst_port,
                "protocol": flow.protocol,
                "bytes": flow.bytes_transferred,
                "duration": flow.duration_seconds,
                "timestamp": flow.timestamp,
                "type": flow.flow_type,
                "tags": flow.tags,
                "attack_type": attack_type,
            })

        self._save_flows(flows, attack_type)
        return flows

    def generate_mixed_traffic(
        self, normal_count: int = 500, malicious_count: int = 50
    ) -> list[dict[str, Any]]:
        """Generate a mix of normal and malicious traffic.

        Args:
            normal_count: Number of normal flows.
            malicious_count: Number of malicious flows.

        Returns:
            List of all generated flow dictionaries.
        """
        normal = self.generate_normal_traffic(normal_count)
        attack_types = ["c2_beacon", "port_scan", "credential_stuffing", "data_exfil"]
        malicious = []
        for i in range(malicious_count):
            attack_type = attack_types[i % len(attack_types)]
            malicious.extend(self.generate_malicious_traffic(attack_type, 1))

        all_flows = normal + malicious
        random.shuffle(all_flows)
        self._save_flows(all_flows, "mixed")
        return all_flows

    def _save_flows(self, flows: list[dict[str, Any]], label: str) -> None:
        """Save flows to a JSON file."""
        path = os.path.join(self.output_dir, f"flows_{label}_{self.session_id}.json")
        with open(path, "w") as f:
            json.dump(flows, f, indent=2)

    def get_statistics(self) -> dict[str, Any]:
        """Return statistics about generated traffic.

        Returns:
            Dictionary of traffic generation statistics.
        """
        stats = dict(self._stats)
        stats["total_flows"] = len(self._flows)
        if self._flows:
            stats["unique_src_ips"] = len(set(f.src_ip for f in self._flows))
            stats["unique_dst_ips"] = len(set(f.dst_ip for f in self._flows))
            stats["total_bytes"] = sum(f.bytes_transferred for f in self._flows)
            stats["malicious_percentage"] = round(
                self._stats["malicious_flows"] / max(self._stats["total_flows"], 1) * 100, 2
            )
        return stats

    def reset(self) -> None:
        """Reset the traffic generator state."""
        self._flows = []
        self._stats = {
            "total_flows": 0,
            "malicious_flows": 0,
            "normal_flows": 0,
            "bytes_transferred": 0,
            "by_protocol": {},
            "by_action": {},
        }
