---
name: autonomous-factory
description: "Autonomous Software Factory - Turns OpenCode into a full autonomous development pipeline from requirements to production deployment using SLDR subagents with artifact handoffs and verification gates."
version: 1.0.0
author: Project Zero
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Autonomous, Factory, SLDR, Subagents, Handoffs, Verification, CI/CD, Full-Stack]
    related_skills: [opencode, autonomous-sdlc-orchestrator, quantum-c2-swarm-orchestrator, agent-team-orchestration]
---

# Autonomous Software Factory Skill

Transforms OpenCode/Z-Code/Z-Fable/OpenFable-v2 from a single coding assistant into an **autonomous software factory** that can go from requirements to a production-deployed application without human intervention.

## Core Architecture

### SLDR Subagent Roles

| Role | Responsibility | Input Contract | Output Contract |
|------|---------------|----------------|-----------------|
| **S** - Strategist | Requirements → Architecture & Task Graph | User requirements, constraints | `architecture.json`, `task-graph.json`, `api-contracts.json` |
| **L** - Lifecycle (Dev) | Architecture → Implementation | `architecture.json`, `task-graph.json` | Source code, `build-report.json`, `test-report.json` |
| **D** - Deploy | Implementation → Production | Source code, `build-report.json` | `deployment-manifests`, `deployment-report.json`, live URL |
| **R** - Review | Quality Gate Enforcement | All artifacts | `gate-results.json`, `security-report.json`, approval/block |

### Artifact-Based Handoffs

All communication between roles happens via **JSON artifacts** in `.opencode/handoffs/` (and equivalent for other agents):

```
.opencode/handoffs/
├── 01-requirements.json          # User input + constraints
├── 02-architecture.json          # System design from Strategist
├── 03-task-graph.json            # Dependency-ordered tasks
├── 04-api-contracts.json         # OpenAPI specs, data models
├── 05-implementation/            # Source code per task
├── 06-build-report.json          # Build + test results
├── 07-security-report.json       # SAST/DAST results
├── 08-deployment-manifests/      # K8s, Docker, Terraform
├── 09-deployment-report.json     # Live URL, health checks
└── 10-gate-results.json          # All verification gate results
```

### Orchestration Rules

1. **Sequential** where dependencies exist: S → L → D (with R gates between)
2. **Parallel** where independent: Multiple L tasks, multiple D targets
3. **Verification Gates** between every handoff:
   - Build gate: `compile`, `type-check`
   - Test gate: `unit`, `integration`, `e2e`
   - Lint gate: `eslint`, `ruff`, `golangci-lint`
   - Security gate: `bandit`, `semgrep`, `trivy`, `snyk`

### Auto-Resume Intelligence

When `/auto` runs:
1. **Scan** `.opencode/handoffs/` for latest completed artifact
2. **Detect** production state via deployment report
3. **Prompt** only for missing requirements/constraints
4. **Resume** from the exact handoff point
5. **Run to completion** without further intervention

## Commands

| Command | Description |
|---------|-------------|
| `/auto` | Run full autonomous factory from current state to production |
| `/auto init` | Initialize new project with requirements gathering |
| `/auto resume` | Resume from last checkpoint |
| `/auto status` | Show current pipeline state |
| `/auto handoff <role>` | Manual handoff trigger |
| `/auto gate <gate>` | Run specific verification gate |

## Quick Start

```bash
# Initialize new project
/auto init

# Or resume existing
/auto resume

# Full autonomous run
/auto
```

## Configuration

```yaml
# .opencode/factory.yaml
factory:
  model: "anthropic/claude-sonnet-4"  # Best available
  parallel_limit: 4
  gates:
    build: true
    test: true
    lint: true
    security: true
  deploy:
    targets: [kubernetes, vercel, aws]
    auto_promote: false
  resume:
    auto_detect: true
    prompt_missing: true
```

## Requirements

- OpenCode/Z-Code/Z-Fable/OpenFable-v2 installed
- Git repository
- At least one LLM provider configured (OpenRouter, Anthropic, etc.)
- Docker for containerized verification gates
- kubectl/vercel/aws CLI for deployment targets