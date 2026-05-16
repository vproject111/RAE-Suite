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

## 🚀 Quick Start

Follow these steps to deploy the entire Silicon Oracle RAE Suite on your system.

### 1. Clone the repository
Ensure you clone recursively to include all specialized agent submodules:
```bash
git clone --recursive https://github.com/dreamsoft-pro/RAE-Suite.git
cd RAE-Suite
```

### 2. Configure Environment
Create a `.env` file with the following default configuration:
```bash
cat <<EOT > .env
RAE_PROFILE=dev
POSTGRES_USER=rae
POSTGRES_PASSWORD=rae
POSTGRES_DB=rae
RAE_API_URL=http://rae-memory:8000
QDRANT_URL=http://rae-am-qdrant:6333
REDIS_URL=redis://rae-am-redis:6379/0
RAE_PROJECT_NAME=dreamsoft_factory
EOT
```

### 3. Launch the Factory
Run the following command to build the agentic images and start all services:
```bash
docker compose up -d --build
```

## ✅ Verification
Check if all containers are running correctly:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

---
**Lead Engineer**: Grzegorz Leśniowski (@vproject111)
**Vision**: Continuous Engineering through Autonomous Reflexive Agents.
