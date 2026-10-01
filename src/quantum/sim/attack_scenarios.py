"""Attack scenario library module.

Catalog of known attack scenarios with detection and mitigation guidance.
"""
from __future__ import annotations

import os
from typing import Any

from dataclasses import dataclass


@dataclass
class AttackScenario:
    id: str
    name: str
    mitre_tactic: str
    mitre_technique: str
    difficulty: str
    detection_method: str
    mitigation: str
    description: str


class AttackScenarioLibrary:
    """Library of documented attack scenarios for simulation and training."""

    PREDEFINED_SCENARIOS: list[AttackScenario] = [
        AttackScenario(
            id="T1566.001", name="Spearphishing Attachment", mitre_tactic="Initial Access",
            mitre_technique="T1566.001", difficulty="low",
            detection_method="Email security gateway, user behavior analytics",
            mitigation="User training, email filtering, macro policies",
            description="Adversary sends a malicious attachment via spearphishing email.",
        ),
        AttackScenario(
            id="T1071.001", name="Web Protocols", mitre_tactic="Command and Control",
            mitre_technique="T1071.001", difficulty="medium",
            detection_method="Network traffic analysis, proxy logs",
            mitigation="Network segmentation, egress filtering, TLS inspection",
            description="Adversary uses web protocols for C2 communication.",
        ),
        AttackScenario(
            id="T1070.004", name="File Deletion", mitre_tactic="Defense Evasion",
            mitre_technique="T1070.004", difficulty="low",
            detection_method="File integrity monitoring, process monitoring",
            mitigation="Least privilege, file system auditing, endpoint protection",
            description="Adversary deletes files to cover tracks.",
        ),
        AttackScenario(
            id="T1055", name="Process Injection", mitre_tactic="Defense Evasion",
            mitre_technique="T1055", difficulty="high",
            detection_method="EDR, behavioral analysis, memory scanning",
            mitigation="AppLocker, EDR, signed code policies",
            description="Adversary injects code into running processes.",
        ),
        AttackScenario(
            id="T1027", name="Obfuscated Files or Information", mitre_tactic="Defense Evasion",
            mitre_technique="T1027", difficulty="medium",
            detection_method="Static analysis, behavioral analysis",
            mitigation="Code signing policies, EDR, application whitelisting",
            description="Adversary obfuscates files to evade detection.",
        ),
        AttackScenario(
            id="T1005", name="Data from Local System", mitre_tactic="Collection",
            mitre_technique="T1005", difficulty="low",
            detection_method="File access monitoring, DLP, EDR",
            mitigation="Data classification, access controls, encryption",
            description="Adversary collects data from local system.",
        ),
        AttackScenario(
            id="T1566", name="Phishing for Credentials", mitre_tactic="Credential Access",
            mitre_technique="T1566", difficulty="low",
            detection_method="User behavior analytics, email security",
            mitigation="MFA, user training, conditional access",
            description="Adversary uses phishing to obtain credentials.",
        ),
        AttackScenario(
            id="T1071", name="Application Layer Protocol", mitre_tactic="Command and Control",
            mitre_technique="T1071", difficulty="medium",
            detection_method="Network traffic analysis, protocol analysis",
            mitigation="Network segmentation, protocol filtering",
            description="Adversary uses application layer protocol for C2.",
        ),
    ]

    def __init__(self, config_path: str | None = None):
        self.scenarios = list(self.PREDEFINED_SCENARIOS)
        self._custom_scenarios: list[AttackScenario] = []
        self.config_path = config_path or os.path.expanduser("~/.quantum/scenarios.json")

    def list_scenarios(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """List all scenarios, optionally filtered."""
        all_scenarios = self.scenarios + self._custom_scenarios
        result = []

        for scenario in all_scenarios:
            if filters:
                match = True
                for key, value in filters.items():
                    if getattr(scenario, key, None) != value:
                        match = False
                        break
                if not match:
                    continue

            result.append({
                "id": scenario.id,
                "name": scenario.name,
                "mitre_tactic": scenario.mitre_tactic,
                "mitre_technique": scenario.mitre_technique,
                "difficulty": scenario.difficulty,
                "detection_method": scenario.detection_method,
                "mitigation": scenario.mitigation,
                "description": scenario.description,
            })

        return result

    def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        """Get a specific scenario by MITRE technique ID."""
        all_scenarios = self.scenarios + self._custom_scenarios
        for scenario in all_scenarios:
            if scenario.id == scenario_id:
                return {
                    "id": scenario.id,
                    "name": scenario.name,
                    "mitre_tactic": scenario.mitre_tactic,
                    "mitre_technique": scenario.mitre_technique,
                    "difficulty": scenario.difficulty,
                    "detection_method": scenario.detection_method,
                    "mitigation": scenario.mitigation,
                    "description": scenario.description,
                }
        return None

    def add_scenario(self, scenario: dict[str, Any]) -> bool:
        """Add a custom attack scenario to the library."""
        try:
            new_scenario = AttackScenario(
                id=scenario["id"],
                name=scenario["name"],
                mitre_tactic=scenario["mitre_tactic"],
                mitre_technique=scenario["mitre_technique"],
                difficulty=scenario.get("difficulty", "medium"),
                detection_method=scenario.get("detection_method", ""),
                mitigation=scenario.get("mitigation", ""),
                description=scenario.get("description", ""),
            )
            self._custom_scenarios.append(new_scenario)
            return True
        except (KeyError, TypeError):
            return False

    def get_statistics(self) -> dict[str, Any]:
        """Return statistics about the scenario library."""
        return {
            "total_scenarios": len(self.scenarios) + len(self._custom_scenarios),
            "built_in_scenarios": len(self.scenarios),
            "custom_scenarios": len(self._custom_scenarios),
            "tactics_covered": list(set(s.mitre_tactic for s in self.scenarios)),
            "difficulty_distribution": {
                "low": sum(1 for s in self.scenarios if s.difficulty == "low"),
                "medium": sum(1 for s in self.scenarios if s.difficulty == "medium"),
                "high": sum(1 for s in self.scenarios if s.difficulty == "high"),
            },
        }
