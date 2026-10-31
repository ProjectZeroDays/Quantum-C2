"""Autonomous Factory Skill Package."""

from .factory import AutonomousFactory, FactoryConfig, Role, PipelineState, HandoffArtifact, VerificationGate, GateStatus, ROLE_DEFINITIONS
from .commands import register_commands

__all__ = [
    "AutonomousFactory",
    "FactoryConfig",
    "Role",
    "PipelineState",
    "HandoffArtifact",
    "VerificationGate",
    "GateStatus",
    "ROLE_DEFINITIONS",
    "register_commands",
]
__version__ = "1.0.0"