# RAE-Suite v4.3: Global AI Engineering Factory 🚀

RAE-Suite is an integrated orchestration environment for intelligent engineering agents. The system operates as an "Autonomous Factory" that designs, develops, tests, and monitors Enterprise-grade software (e.g., ScreenWatcher, Billboard Marker).

## 🏗️ Factory Architecture (Quantum Ready)

The system consists of 5 specialized modules connected into a single neural network:

1.  **[RAE-agentic-memory](packages/rae-core)**: The Quantum Intelligence Core. Manages semantic knowledge and reflection.
2.  **[RAE-Phoenix](packages/rae-phoenix)**: Lead Architect and Developer. Generates code and plans refactoring.
3.  **[RAE-Hive](packages/rae-hive)**: Execution Layer (The Hands). Runs scripts, containers, and performs visual audits (Playwright).
4.  **[RAE-Quality](packages/rae-quality)**: Autonomous Quality Guard. Performs continuous security testing (SAST) and verifies code coverage.
5.  **[RAE-Lab](packages/rae-lab)**: Intelligence Observatory. Analyzes experiment results and implements the Kaizen strategy (continuous improvement).

## 🛡️ Standards & Security
*   **ISO 27001 Compliance**: Full separation of duties and auditability of every agent action.
*   **Hard Frames 2.1**: Rigorous contractual frameworks preventing AI hallucinations.
*   **Telemetry**: Full operational metric coverage displayed in a central Grafana dashboard.

## 🚀 Quick Start & Installation

RAE-Suite leverages the **Cardinal RAE Principle (Data Isolation Mandate)**: databases and persistent cognitive layers are strictly separated from Docker containers to protect knowledge from resets. 

The installation process dynamically handles host path configuration, SQL backups, and enforces the Hybrid Search Strategy.

### 1. Clone the repository recursively
To ensure all specialized agent submodules are cloned, pull them recursively:
```bash
git clone --recursive https://github.com/vproject111/RAE-Suite.git
cd RAE-Suite
```

### 2. Run the Interactive Setup
Configure the environment variables, persistent database directory on the host, and import SQL dumps interactively:
```bash
./setup.sh
```
*Note: If you run `./start.sh` without prior setup, the Startup Guard will automatically trigger `./setup.sh` first.*

---

## 🎭 Execution Profiles

You can start the RAE-Suite Factory in two distinct modes:

### A. Production Profile (Standard Mode)
Best for production runs, background tasks, and stable evaluations.
```bash
./start.sh
```
*(Or standard: `docker compose up -d --build`)*

### B. Development Profile (Hot-Reload Mode)
Best for developers. It boots uvicorn with `--reload`, binds source code volumes for `rae-core`, `rae-hive`, `rae-quality`, `rae-lab`, and `rae-phoenix`, allowing your live edits to be reflected immediately inside the running containers.
```bash
./start.sh --dev
```
*(Or manually: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build`)*

---

## ✅ Verification
Ensure all suite modules are healthy and running:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

To view live telemetry logs of the Memory cognitive layer:
```bash
docker logs -f rae-memory
```

---
**Lead Engineer**: Grzegorz Leśniowski (@vproject111)
**Vision**: Continuous Engineering through Autonomous Reflexive Agents.
