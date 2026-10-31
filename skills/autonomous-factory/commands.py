#!/usr/bin/env python3
"""
Autonomous Factory Command Registration for OpenCode/Z-Code/Z-Fable/OpenFable-v2
Registers the /auto command with intelligent autocomplete.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add skill directory to path
SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))

from factory import AutonomousFactory, FactoryConfig, Role, PipelineState, HandoffArtifact


def register_commands(registry) -> None:
    """Register Autonomous Factory commands with the command registry."""
    
    # Register the main /auto command
    registry.register_command(
        name="auto",
        description="Autonomous Software Factory - Run full pipeline from requirements to production",
        handler=handle_auto_command,
        completer=auto_completer,
        aliases=["factory", "sldr", "autonomous"],
    )


def handle_auto_command(args: list, context: dict) -> dict:
    """Handle the /auto command."""
    import asyncio
    
    # Parse subcommand
    subcommand = args[0] if args else "run"
    sub_args = args[1:] if len(args) > 1 else []
    
    # Load config
    config_path = Path(".opencode/factory.yaml")
    config = FactoryConfig.load(config_path)
    
    factory = AutonomousFactory(config)
    
    async def run_async():
        if subcommand == "init":
            return await handle_init(factory, sub_args)
        elif subcommand == "status":
            return await handle_status(factory)
        elif subcommand == "resume":
            return await handle_resume(factory)
        elif subcommand == "handoff":
            return await handle_handoff(factory, sub_args)
        elif subcommand == "gate":
            return await handle_gate(factory, sub_args)
        else:  # run
            return await handle_run(factory, sub_args)
    
    result = asyncio.run(run_async())
    return result


async def handle_init(factory: AutonomousFactory, args: list) -> dict:
    """Initialize new project with requirements gathering."""
    print("=== Autonomous Factory Initialization ===")
    
    requirements = {}
    requirements["project_type"] = input("Project type (web/api/mobile/cli): ") or "web"
    requirements["tech_stack"] = input("Tech stack (nodejs/python/go/rust): ") or "nodejs"
    requirements["deployment_target"] = input("Deployment target (kubernetes/vercel/aws): ") or "kubernetes"
    requirements["database"] = input("Database (postgresql/mongodb/redis): ") or "postgresql"
    features_input = input("Key features (comma-separated): ")
    requirements["features"] = [f.strip() for f in features_input.split(",")] if features_input else []
    requirements["scale"] = input("Scale (small/medium/large): ") or "medium"
    
    req_artifact = HandoffArtifact(
        id="req-" + str(hash(str(requirements)))[:8],
        role=Role.STRATEGIST,
        name="requirements",
        version=1,
        timestamp="",
        content=requirements
    )
    req_artifact.timestamp = ""
    req_artifact.to_file(factory.handoff_dir)
    
    return {
        "ok": True,
        "type": "init",
        "message": "Requirements saved. Run '/auto' to start the pipeline.",
        "requirements": requirements
    }


async def handle_status(factory: AutonomousFactory) -> dict:
    """Show current pipeline state."""
    state = factory.load_state()
    prod = factory.detect_production_state()
    missing = factory.get_missing_requirements()
    
    # Load gate results if available
    gate_results = {}
    gate_file = factory.handoff_dir / "gate-results.json"
    if gate_file.exists():
        with open(gate_file) as f:
            gate_results = json.load(f)
    
    return {
        "ok": True,
        "type": "status",
        "pipeline_state": state.value,
        "production": prod,
        "missing_requirements": missing,
        "gates": gate_results,
        "handoff_dir": str(factory.handoff_dir)
    }


async def handle_resume(factory: AutonomousFactory) -> dict:
    """Resume from last checkpoint."""
    state = factory.load_state()
    return {
        "ok": True,
        "type": "resume",
        "message": f"Resuming from {state.value}",
        "state": state.value
    }


async def handle_handoff(factory: AutonomousFactory, args: list) -> dict:
    """Manual handoff trigger for specific role."""
    if not args:
        return {"ok": False, "error": "Role required. Usage: /auto handoff <role>"}
    
    role_name = args[0].lower()
    try:
        role = Role(role_name)
    except ValueError:
        return {"ok": False, "error": f"Invalid role: {role_name}. Valid: {[r.value for r in Role]}"}
    
    # Run specific role
    async def run_role():
        if role == Role.STRATEGIST:
            return await factory.run_strategist()
        elif role == Role.LIFECYCLE:
            return await factory.run_lifecycle()
        elif role == Role.DEPLOY:
            return await factory.run_deploy()
        elif role == Role.REVIEW:
            return await factory.run_review()
    
    artifact = await run_role()
    return {
        "ok": True,
        "type": "handoff",
        "role": role.value,
        "artifact": artifact.name if artifact else None
    }


async def handle_gate(factory: AutonomousFactory, args: list) -> dict:
    """Run specific verification gate."""
    if not args:
        return {"ok": False, "error": "Gate name required. Usage: /auto gate <gate>"}
    
    gate_name = args[0].lower()
    valid_gates = ["build", "test", "lint", "security"]
    
    if gate_name not in valid_gates:
        return {"ok": False, "error": f"Invalid gate: {gate_name}. Valid: {valid_gates}"}
    
    gate = await factory.run_gate(gate_name, Role.REVIEW)
    
    return {
        "ok": True,
        "type": "gate",
        "gate": gate_name,
        "status": gate.status.value,
        "output": gate.output,
        "errors": gate.errors
    }


async def handle_run(factory: AutonomousFactory, args: list) -> dict:
    """Run full pipeline."""
    # Check for requirements file argument
    requirements = None
    if args and args[0].endswith(".json"):
        with open(args[0]) as f:
            requirements = json.load(f)
    
    result = await factory.run_full_pipeline(requirements)
    return {
        "ok": result.get("status") not in ["failed", "blocked", "needs_requirements"],
        "type": "run",
        "result": result
    }


def auto_completer(partial: str, context: dict) -> list:
    """Autocomplete for /auto command."""
    subcommands = [
        {"name": "run", "description": "Run full autonomous pipeline (default)"},
        {"name": "init", "description": "Initialize new project with requirements gathering"},
        {"name": "resume", "description": "Resume from last checkpoint"},
        {"name": "status", "description": "Show current pipeline state"},
        {"name": "handoff", "description": "Manual handoff trigger for specific role"},
        {"name": "gate", "description": "Run specific verification gate"},
    ]
    
    # Filter by partial input
    partial_lower = partial.lower()
    filtered = [c for c in subcommands if c["name"].startswith(partial_lower)]
    
    return [
        {
            "label": c["name"],
            "description": c["description"],
            "insertText": c["name"],
            "kind": "method"
        }
        for c in filtered
    ]


# For direct testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto Command Test")
    parser.add_argument("subcommand", nargs="?", default="status")
    parser.add_argument("args", nargs="*")
    
    args = parser.parse_args()
    
    class MockRegistry:
        def register_command(self, **kwargs):
            print(f"Registered command: {kwargs['name']}")
    
    register_commands(MockRegistry())
    
    # Test completer
    print("\n=== Autocomplete Tests ===")
    for query in ["", "r", "re", "run", "in", "ha", "ga"]:
        results = auto_completer(query, {})
        print(f"  /auto {query} -> {[r['label'] for r in results]}")