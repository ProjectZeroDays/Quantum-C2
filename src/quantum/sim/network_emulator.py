"""Network emulation module for network simulation.

Creates virtual network topologies and simulates network activity.
"""
from __future__ import annotations

import json
import os
import uuid
import random
from datetime import datetime
from typing import Any
from dataclasses import dataclass, field


@dataclass
class NetworkNode:
    id: str
    name: str
    ip: str
    type: str  # "server", "workstation", "router", "switch", "firewall"
    role: str  # "critical", "standard", "infected", "monitoring"
    status: str  # "up", "down", "compromised"
    subnet: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "ip": self.ip,
            "type": self.type,
            "role": self.role,
            "status": self.status,
            "subnet": self.subnet,
        }


@dataclass
class NetworkLink:
    source: str
    target: str
    bandwidth: str
    latency: str
    protocol: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "bandwidth": self.bandwidth,
            "latency": self.latency,
            "protocol": self.protocol,
        }


class NetworkEmulator:
    """Emulates network topologies and traffic patterns."""

    NODE_TYPES = {
        "server": ["web", "database", "app", "dns", "mail", "file", "domain_controller"],
        "workstation": ["user", "admin", "dev", "finance"],
        "router": ["edge", "core", "distribution"],
        "switch": ["access", "aggregation"],
        "firewall": ["perimeter", "internal"],
    }

    def __init__(self, output_dir: str = "/tmp/quantum_simulations/network"):
        self.output_dir = output_dir
        self.session_id = str(uuid.uuid4())
        self._nodes: dict[str, NetworkNode] = {}
        self._links: list[NetworkLink] = []
        self._traffic_log: list[dict[str, Any]] = []
        os.makedirs(self.output_dir, exist_ok=True)

    def _generate_ip(self, subnet: str) -> str:
        """Generate an IP within a subnet."""
        base = int(subnet.split(".")[2])
        return f"10.{base}.{random.randint(1, 254)}.{random.randint(2, 254)}"

    def create_topology(self, config: dict[str, Any]) -> dict[str, Any]:
        """Create a virtual network topology.

        Args:
            config: Topology configuration with keys like:
                - subnets: Number of subnets
                - hosts_per_subnet: Nodes per subnet
                - role_distribution: Optional role weighting

        Returns:
            Dictionary describing the created topology.
        """
        subnets_count = config.get("subnets", 3)
        hosts_per_subnet = config.get("hosts_per_subnet", 10)

        self._nodes.clear()
        self._links.clear()

        node_id_counter = 0

        # Create subnets and nodes
        subnets = []
        for s in range(subnets_count):
            subnet_addr = f"10.{s + 1}.0.0"
            subnets.append(subnet_addr)

            # Create router for subnet
            router_id = f"router-{s}"
            router = NetworkNode(
                id=router_id,
                name=f"Router-S{ s }",
                ip=f"10.{s + 1}.0.1",
                type="router",
                role="standard",
                status="up",
                subnet=subnet_addr,
            )
            self._nodes[router_id] = router
            node_id_counter += 1

            # Create hosts
            for h in range(hosts_per_subnet):
                node_type = random.choices(
                    ["server", "workstation", "router", "switch", "firewall"],
                    weights=[0.15, 0.6, 0.1, 0.1, 0.05],
                )[0]

                role_pool = self.NODE_TYPES.get(node_type, ["standard"])
                role = random.choice(role_pool) if role_pool else "standard"

                node_name = f"{node_type.capitalize()}-{s}-{h}"
                node = NetworkNode(
                    id=f"node-{node_id_counter}",
                    name=node_name,
                    ip=self._generate_ip(subnet_addr),
                    type=node_type,
                    role=role,
                    status=random.choice(["up", "up", "up", "down"]) if random.random() < 0.9 else "compromised",
                    subnet=subnet_addr,
                )
                self._nodes[node.id] = node
                node_id_counter += 1

                # Create link from router to node
                self._links.append(NetworkLink(
                    source=router_id,
                    target=node.id,
                    bandwidth=f"{random.randint(100, 1000)}Mbps",
                    latency=f"{random.randint(1, 50)}ms",
                    protocol="Ethernet",
                ))

        # Connect subnets with routers
        for i in range(len(subnets) - 1):
            self._links.append(NetworkLink(
                source=f"router-{i}",
                target=f"router-{i + 1}",
                bandwidth="10Gbps",
                latency=f"{random.randint(5, 50)}ms",
                protocol="OSPF",
            ))

        topology_dict = {
            "topology_id": self.session_id,
            "subnets": subnets,
            "total_subnets": len(subnets),
            "total_hosts": hosts_per_subnet * subnets_count,
            "total_nodes": len(self._nodes),
            "total_links": len(self._links),
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "links": [l.to_dict() for l in self._links],
        }

        self._save_topology(topology_dict)
        return topology_dict

    def simulate_network_activity(self, duration_minutes: int = 30) -> list[dict[str, Any]]:
        """Simulate network activity over a period.

        Args:
            duration_minutes: How long to simulate in minutes.

        Returns:
            List of simulated flow records.
        """
        if not self._nodes:
            self.create_topology({"subnets": 2, "hosts_per_subnet": 10})

        flows = []
        flows_per_minute = 50
        total_flows = min(int(duration_minutes * flows_per_minute), 5000)

        for i in range(total_flows):
            src_node = random.choice(list(self._nodes.values()))
            potential_targets = [n for n in self._nodes.values() if n != src_node]

            if not potential_targets:
                continue

            dst_node = random.choice(potential_targets)

            flow = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "src_ip": src_node.ip,
                "dst_ip": dst_node.ip,
                "src_port": random.randint(1024, 65535),
                "dst_port": random.choice([80, 443, 22, 3389, 53, 445, 3306, 5432]),
                "protocol": random.choice(["TCP", "UDP"]),
                "bytes": random.randint(64, 1000000),
                "duration_ms": random.randint(1, 5000),
                "flow_type": random.choices(["normal", "malicious"], weights=[90, 10])[0],
                "src_node": src_node.name,
                "dst_node": dst_node.name,
                "src_role": src_node.role,
                "dst_role": dst_node.role,
            }
            flows.append(flow)
            self._traffic_log.append(flow)

        self._save_flows(flows)
        return flows

    def get_topology_summary(self) -> dict[str, Any]:
        """Return a summary of the current topology."""
        role_distribution = {}
        for node in self._nodes.values():
            role_distribution[node.role] = role_distribution.get(node.role, 0) + 1

        type_distribution = {}
        for node in self._nodes.values():
            type_distribution[node.type] = type_distribution.get(node.type, 0) + 1

        status_distribution = {}
        for node in self._nodes.values():
            status_distribution[node.status] = status_distribution.get(node.status, 0) + 1

        return {
            "total_nodes": len(self._nodes),
            "total_links": len(self._links),
            "role_distribution": role_distribution,
            "type_distribution": type_distribution,
            "status_distribution": status_distribution,
            "traffic_logs": len(self._traffic_log),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def _save_topology(self, topology: dict[str, Any]) -> None:
        """Save topology to file."""
        path = os.path.join(self.output_dir, f"topology_{self.session_id}.json")
        with open(path, "w") as f:
            json.dump(topology, f, indent=2)

    def _save_flows(self, flows: list[dict[str, Any]]) -> None:
        """Save flows to file."""
        path = os.path.join(self.output_dir, f"activity_{self.session_id}.json")
        with open(path, "w") as f:
            json.dump(flows, f, indent=2)
