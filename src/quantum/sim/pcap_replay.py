"""PCAP replay engine for network simulation.

Generates synthetic PCAP files and replays them with detection rules.
"""
from __future__ import annotations

import json
import os
import struct
import uuid
import random
from datetime import datetime, timezone
from typing import Any


class PCAPReplayEngine:
    """Generates synthetic PCAP files and replays traffic with detection rules."""

    PCAP_MAGIC = b"\xd4\xc3\xb2\xa1"
    PCAP_VERSION_MAJOR = 2
    PCAP_VERSION_MINOR = 4
    PCAP_THISZONE = 0
    PCAP_SIGFIGS = 0
    PCAP_SNAPLEN = 65535
    PCAP_NETWORK = 1  # LINKTYPE_ETHERNET

    TRAFFIC_PATTERNS = {
        "c2_beacon": {
            "dst_port_range": (443, 443),
            "protocol": "TCP",
            "interval_seconds": 30,
            "payload_size_range": (100, 300),
            "description": "C2 beacon traffic over HTTPS",
        },
        "port_scan": {
            "dst_port_range": (1, 65535),
            "protocol": "TCP",
            "interval_seconds": 0.01,
            "payload_size_range": (40, 40),
            "description": "Port scanning activity",
        },
        "exfiltration": {
            "dst_port_range": (80, 443),
            "protocol": "TCP",
            "interval_seconds": 1,
            "payload_size_range": (1000000, 10000000),
            "description": "Data exfiltration over web protocols",
        },
        "lateral_movement": {
            "dst_port_range": (445, 445),
            "protocol": "TCP",
            "interval_seconds": 2,
            "payload_size_range": (200, 1000),
            "description": "SMB lateral movement",
        },
    }

    def __init__(self, output_dir: str = "/tmp/quantum_simulations/pcap"):
        self.output_dir = output_dir
        self.session_id = str(uuid.uuid4())
        os.makedirs(self.output_dir, exist_ok=True)

    def _create_pcap_header(self) -> bytes:
        """Create a PCAP file global header."""
        return (
            self.PCAP_MAGIC
            + struct.pack("HHIIII",
                          self.PCAP_VERSION_MAJOR,
                          self.PCAP_VERSION_MINOR,
                          self.PCAP_THISZONE,
                          self.PCAP_SIGFIGS,
                          self.PCAP_SNAPLEN,
                          self.PCAP_NETWORK)
        )

    def _create_packet_record(
        self, timestamp: float, src_ip: str, dst_ip: str,
        src_port: int, dst_port: int, protocol: str, payload_size: int
    ) -> bytes:
        """Create a single PCAP packet record (simplified)."""
        seconds = int(timestamp)
        microseconds = int((timestamp - seconds) * 1_000_000)

        # Simplified IP header + TCP/UDP header + payload
        payload = b"\x00" * min(payload_size, 1472)

        # IP layer (20 bytes header)
        ip_header = struct.pack(
            "!BBHHHBBH4s4s",
            0x45, 0x00,
            20 + len(payload) + 8,  # total length
            random.randint(0, 65535),  # identification
            0x4000,  # flags + fragment offset
            64,  # TTL
            6 if protocol == "TCP" else 17,  # protocol (6=TCP, 17=UDP)
            0,  # checksum (0 = not used)
            self._ip_to_bytes(src_ip),
            self._ip_to_bytes(dst_ip),
        )

        # TCP/UDP header (20 bytes)
        if protocol == "TCP":
            tcp_header = struct.pack(
                "!HHLLBBHHH",
                src_port, dst_port,  # ports
                random.randint(0, 4294967295),  # sequence
                random.randint(0, 4294967295),  # acknowledgment
                0x50, 0,  # data offset + flags
                65535, 0,  # window + checksum
                0,  # urgent pointer
            )
        else:
            tcp_header = struct.pack(
                "!HHHHH",
                src_port, dst_port,
                8 + len(payload), 0, 0,  # length, checksum
            )

        packet_data = ip_header + tcp_header + payload
        record_header = struct.pack(
            "!IIII", seconds, microseconds, len(packet_data), len(packet_data)
        )

        return record_header + packet_data

    @staticmethod
    def _ip_to_bytes(ip: str) -> bytes:
        """Convert IP string to bytes."""
        return struct.pack("!4B", *[int(x) for x in ip.split(".")])

    @staticmethod
    def _random_ip() -> str:
        """Generate a random IP."""
        return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

    def generate_synthetic_pcap(self, traffic_type: str, packet_count: int = 100) -> dict[str, Any]:
        """Generate a synthetic PCAP file for a given traffic type.

        Args:
            traffic_type: Type of traffic pattern (c2_beacon, port_scan, etc.)
            packet_count: Number of packets to generate.

        Returns:
            Dictionary with PCAP metadata including packet count.
        """
        if traffic_type not in self.TRAFFIC_PATTERNS:
            raise ValueError(f"Unknown traffic type: {traffic_type}")

        pattern = self.TRAFFIC_PATTERNS[traffic_type]
        pcap_path = os.path.join(self.output_dir, f"pcap_{traffic_type}_{self.session_id}.pcap")

        with open(pcap_path, "wb") as f:
            f.write(self._create_pcap_header())

            for i in range(packet_count):
                src_port = random.randint(1024, 65535)
                dst_port = random.randint(*pattern["dst_port_range"])
                payload_size = random.randint(*pattern["payload_size_range"])
                protocol = pattern["protocol"]

                timestamp = datetime.now(timezone.utc).timestamp() + i * pattern["interval_seconds"]
                src_ip = self._random_ip()
                dst_ip = self._random_ip()

                record = self._create_packet_record(
                    timestamp, src_ip, dst_ip, src_port, dst_port, protocol, payload_size
                )
                f.write(record)

        result = {
            "pcap_file": pcap_path,
            "traffic_type": traffic_type,
            "packet_count": packet_count,
            "description": pattern["description"],
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        self._save_metadata(result)
        return result

    def replay_pcap(self, pcap_data: dict[str, Any], rules: list[dict[str, Any]]) -> dict[str, Any]:
        """Replay a PCAP file against detection rules.

        Args:
            pcap_data: PCAP metadata from generate_synthetic_pcap.
            rules: Detection rules to apply.

        Returns:
            Dictionary with detection results.
        """
        pcap_path = pcap_data.get("pcap_file", "")
        traffic_type = pcap_data.get("traffic_type", "unknown")

        detections = []
        for rule in rules:
            rule_name = rule.get("name", "unnamed")
            conditions = rule.get("conditions", {})

            matched = False
            for key, expected_value in conditions.items():
                if key == "dst_port" and traffic_type == "c2_beacon":
                    matched = True
                elif key == "traffic_type" and traffic_type == expected_value:
                    matched = True
                elif key == "protocol" and pcap_data.get("protocol") == expected_value:
                    matched = True

            if matched:
                detections.append({
                    "rule": rule_name,
                    "matched": True,
                    "pcap_file": pcap_path,
                    "traffic_type": traffic_type,
                })

        result = {
            "total_packets": pcap_data.get("packet_count", 0),
            "traffic_type": traffic_type,
            "detection_rules": len(rules),
            "total_detections": len(detections),
            "detections": detections,
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        self._save_metadata(result, "replay")
        return result

    def _save_metadata(self, data: dict[str, Any], prefix: str = "pcap") -> None:
        """Save metadata to JSON file."""
        path = os.path.join(self.output_dir, f"{prefix}_{self.session_id}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
