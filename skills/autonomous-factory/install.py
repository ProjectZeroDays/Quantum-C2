#!/usr/bin/env python3
"""
Autonomous Factory Skill Installer for OpenCode/Z-Code/Z-Fable/OpenFable-v2
Installs the skill and agent into target applications.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def find_target_config_dirs() -> list[Path]:
    """Find possible configuration directories for OpenCode/Z-Code/Z-Fable/OpenFable-v2."""
    home = Path.home()
    dirs = []

    # OpenCode
    dirs.append(home / ".opencode" / "skills")
    dirs.append(home / ".config" / "opencode" / "skills")

    # Z-Code
    dirs.append(home / ".zcode" / "skills")
    dirs.append(home / ".config" / "zcode" / "skills")

    # Z-Fable
    dirs.append(home / ".zfable" / "skills")
    dirs.append(home / ".config" / "zfable" / "skills")

    # OpenFable-v2
    dirs.append(home / ".openfable" / "skills")
    dirs.append(home / ".config" / "openfable" / "skills")

    # Cursor
    dirs.append(home / ".cursor" / "skills")
    dirs.append(home / ".config" / "cursor" / "skills")

    # Generic
    dirs.append(home / ".local" / "share" / "skills")

    return [d for d in dirs if d.exists() or d.parent.exists()]


def install_skill(target_dir: Path, source_dir: Path) -> bool:
    """Install the Autonomous Factory skill to target directory."""
    try:
        target_skill_dir = target_dir / "autonomous-factory"
        target_skill_dir.mkdir(parents=True, exist_ok=True)

        # Copy skill files
        for file in ["SKILL.md", "factory.py", "commands.py", "plugin.json", "__init__.py"]:
            src = source_dir / file
            if src.exists():
                shutil.copy2(src, target_skill_dir / file)
                print("  Copied " + file)

        print("[OK] Installed Autonomous Factory skill to " + str(target_skill_dir))
        return True
    except Exception as e:
        print("[FAIL] Failed to install to " + str(target_dir) + ": " + str(e))
        return False


def install_agent(target_dir: Path, source_file: Path) -> bool:
    """Install the Autonomous Factory agent to target directory."""
    try:
        target_agent_dir = target_dir / "agents"
        target_agent_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_agent_dir / "autonomous-factory.json"
        shutil.copy2(source_file, target_file)
        print("[OK] Installed Autonomous Factory agent to " + str(target_file))
        return True
    except Exception as e:
        print("[FAIL] Failed to install agent to " + str(target_dir) + ": " + str(e))
        return False


def create_factory_config(target_dir: Path) -> bool:
    """Create default factory.yaml config."""
    try:
        config_dir = target_dir / ".opencode"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "factory.yaml"
        
        if not config_file.exists():
            config_content = """factory:
  model: "anthropic/claude-sonnet-4"
  parallel_limit: 4
  gates:
    build: true
    test: true
    lint: true
    security: true
  deploy:
    targets: [kubernetes, vercel, aws]
    auto_promote: false
  handoff_dir: ".opencode/handoffs"
  workspace: "."
"""
            with open(config_file, "w") as f:
                f.write(config_content)
            print("[OK] Created factory config at " + str(config_file))
        return True
    except Exception as e:
        print("[FAIL] Failed to create config: " + str(e))
        return False


def main():
    """Main installer."""
    print("=== Autonomous Factory Skill Installer ===\n")

    # Source paths
    project_root = Path(__file__).parent.parent.parent
    skill_source = project_root / "skills" / "autonomous-factory"
    
    # Create agent JSON for installation
    agent_source = project_root / "src" / "agents" / "autonomous-factory.json"
    agent_source.parent.mkdir(parents=True, exist_ok=True)
    
    agent_data = {
        "id": "autonomous-factory",
        "name": "Autonomous Factory",
        "role": "orchestrator",
        "autonomy": 5,
        "provider": "",
        "model": "anthropic/claude-sonnet-4",
        "system_prompt": "You are the Autonomous Factory orchestrator. You coordinate four specialized SLDR subagents:\n\n1. STRATEGIST - Transforms requirements into architecture, task graphs, and API contracts\n2. LIFECYCLE - Implements architecture as clean, tested, production-ready code\n3. DEPLOY - Deploys validated code to production infrastructure with manifests\n4. REVIEW - Enforces quality gates (build, test, lint, security) between every handoff\n\nAll communication happens via JSON artifacts in .opencode/handoffs/. The pipeline:\n- Runs sequentially where dependencies exist (S -> L -> D with R gates between)\n- Runs in parallel where independent (multiple L tasks, multiple D targets)\n- Has verification gates between every handoff\n- Auto-resumes from last checkpoint when /auto is invoked\n- Prompts only for missing requirements\n- Runs to completion without human intervention",
        "description": "Orchestrates SLDR subagents to autonomously build, test, and deploy full-stack applications from requirements to production.",
        "tags": ["orchestrator", "autonomous", "factory", "sldr", "ci-cd", "deployment"],
        "capabilities": [
            "requirements-analysis",
            "architecture-design",
            "task-graph-generation",
            "api-contract-design",
            "full-stack-implementation",
            "test-generation",
            "deployment-manifest-generation",
            "production-deployment",
            "quality-gate-enforcement",
            "security-scanning",
            "auto-resume",
            "parallel-execution"
        ],
        "commands": {
            "auto": {
                "description": "Autonomous Software Factory - Run full pipeline from requirements to production",
                "subcommands": {
                    "init": "Initialize new project with requirements gathering",
                    "resume": "Resume from last checkpoint",
                    "status": "Show current pipeline state",
                    "handoff": "Manual handoff trigger for specific role",
                    "gate": "Run specific verification gate"
                }
            }
        }
    }
    
    with open(agent_source, "w") as f:
        json.dump(agent_data, f, indent=2)

    print("Source skill: " + str(skill_source))
    print("Source agent: " + str(agent_source))
    print()

    # Find target directories
    target_dirs = find_target_config_dirs()

    if not target_dirs:
        print("No target configuration directories found.")
        print("Please specify target manually or ensure OpenCode/Z-Code/Z-Fable/OpenFable-v2 is installed.")
        return 1

    print("Found target directories:")
    for d in target_dirs:
        print("  " + str(d))
    print()

    # Install to all found directories
    success_count = 0
    for target in target_dirs:
        print("Installing to " + str(target) + "...")
        if install_skill(target, skill_source):
            success_count += 1
        if install_agent(target, agent_source):
            success_count += 1
        create_factory_config(target)

    print("\n=== Installation Complete ===")
    print("Successfully installed to " + str(success_count) + " locations")

    # Also install to project's local skills/agents for Quantum CLI
    print("\nInstalling to Quantum CLI project...")
    quantum_skills = project_root / "src" / "skills"
    quantum_agents = project_root / "src" / "agents"

    if install_skill(quantum_skills, skill_source):
        success_count += 1
    if install_agent(quantum_agents, agent_source):
        success_count += 1
    create_factory_config(project_root / "src")

    print("\nTotal installations: " + str(success_count))
    print("\nNext steps:")
    print("1. Restart OpenCode/Z-Code/Z-Fable/OpenFable-v2")
    print("2. The 'Autonomous Factory' agent will appear in the agent dropdown")
    print("3. Use '/auto' for intelligent autocomplete")
    print("4. Run '/auto init' to start a new project")
    print("5. Run '/auto' to execute full pipeline")

    return 0


if __name__ == "__main__":
    sys.exit(main())