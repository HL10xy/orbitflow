# 🚀 OrbitFlow — Multi-Agent Software Engineering Framework

**A production-grade multi-agent collaboration framework that orchestrates specialized AI agents to automate complex software engineering workflows.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)

---

## 📖 Overview

OrbitFlow implements a **multi-agent pipeline architecture** where four specialized AI agents — **Architect, Coder, Reviewer, and Tester** — collaborate through a shared memory space to solve complex software engineering tasks end-to-end.

### Why Multi-Agent?

Single-agent LLM workflows hit diminishing returns on complex, long-context tasks. OrbitFlow decomposes each task into dependency-ordered sub-tasks, assigns each to a role-specialized agent, and orchestrates their collaboration through **shared memory** and **structured handoffs** — enabling deeper reasoning, better code quality, and higher token utilization efficiency.

```
┌──────────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  🏗️ Architect  │───▶│  💻 Coder  │───▶│ 🔍 Reviewer │───▶│  🧪 Tester  │
│  Design &     │    │ Implement │    │ Review &  │    │ Test &    │
│  Planning     │    │ Core Logic│    │ Validate  │    │ Verify    │
└──────────────┘    └──────────┘    └──────────┘    └──────────┘
        │                  │                 │                 │
        └──────────────────┴─────────────────┴─────────────────┘
                            Shared Memory
```

## 🧠 Architecture

| Component | Technology | Description |
|-----------|-----------|-------------|
| **Agent Engine** | Python 3.10+ | Role-based agents with configurable system prompts |
| **Orchestrator** | Python (asyncio) | Task decomposition, dependency resolution, pipeline execution |
| **Shared Memory** | Python (OrderedDict) | Thread-safe inter-agent communication with eviction |
| **LLM Client** | httpx | OpenAI-compatible API client (MiMo, OpenAI, any provider) |
| **API Server** | FastAPI + WebSocket | REST API + real-time streaming endpoints |
| **CLI Tool** | Click + Rich | Terminal-based pipeline runner with live status |
| **Dashboard** | React 18 + TypeScript | Real-time visualization of agent collaboration |
| **Pipeline** | Python (asyncio) | DAG-based sub-task execution with event streaming |

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- An OpenAI-compatible API key (MiMo, OpenAI, or any compatible provider)

### 1. Clone & Setup Backend

```bash
git clone https://github.com/YOUR_USERNAME/orbitflow.git
cd orbitflow

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Configure your LLM provider
export LLM_BASE_URL="https://api.xiaomimimo.com/v1"  # MiMo
export LLM_API_KEY="your-api-key-here"
export LLM_MODEL="mimo-v2.5-pro"
```

### 2. Run via CLI

```bash
# Run a task through the multi-agent pipeline
python -m cli.main run "Build a REST API for user authentication with JWT"

# Run with higher complexity (more agents, more iterations)
python -m cli.main run --complexity epic "Design a distributed rate limiter"

# Start the API server
python -m cli.main serve
```

### 3. Run with Web Dashboard

```bash
# Terminal 1: Start the backend
cd backend
python main.py

# Terminal 2: Start the frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 to see the real-time multi-agent collaboration dashboard.

## 🔌 Supported LLM Providers

OrbitFlow uses an OpenAI-compatible API interface, making it pluggable with:

- **Xiaomi MiMo** — `https://api.xiaomimimo.com/v1`
- **OpenAI** — `https://api.openai.com/v1`
- **Anthropic Claude** (via compatible proxy)
- **Any OpenAI-compatible endpoint** (vLLM, Ollama, LiteLLM, etc.)

## 🎯 Key Features

### Multi-Agent Collaboration
Four specialized agents, each with role-specific system prompts, communicate through shared memory to solve tasks beyond single-agent capability.

### Long-Chain Reasoning
Tasks are decomposed into dependency-ordered sub-tasks. Each agent builds on the output of previous agents, enabling deep, multi-step reasoning chains.

### Real-Time Visualization
A React dashboard shows the pipeline flow, agent status, and live communication log via WebSocket streaming.

### Pluggable LLM Backend
Swap the underlying model without changing code. Configure via environment variables or the runtime API.

### Dual Interface
- **CLI** for developers who live in the terminal
- **Web Dashboard** for demos, monitoring, and team collaboration

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/status` | Orchestrator status and memory snapshot |
| `POST` | `/task/run` | Run a task (non-streaming) |
| `POST` | `/config/llm` | Update LLM configuration |
| `WS` | `/ws` | Real-time agent collaboration stream |

### WebSocket Protocol

```json
// Send a task
{"action": "run", "description": "Build a todo API", "complexity": "moderate"}

// Receive real-time events
{"event_type": "agent_start", "agent": "architect", "message": "..."}
{"event_type": "agent_end", "agent": "architect"}
{"event_type": "agent_start", "agent": "coder", "message": "..."}
{"event_type": "task_end", "message": "Task completed: ..."}
```

## 🏗️ Task Complexity Levels

| Level | Agents | Flow | Token Usage |
|-------|--------|------|-------------|
| **Simple** | 2 (Architect → Coder) | Linear | Low |
| **Moderate** | 4 (Architect → Coder → Reviewer → Tester) | Sequential | Medium |
| **Complex** | 4 with multiple rounds | Iterative refinement | High |
| **Epic** | 4 with parallel sub-tasks | Full DAG pipeline | Very High |

## 📁 Project Structure

```
orbitflow/
├── backend/
│   ├── agents/           # Specialized AI agents
│   │   ├── base.py       # Abstract base agent
│   │   ├── architect.py  # System design agent
│   │   ├── coder.py      # Code generation agent
│   │   ├── reviewer.py   # Code review agent
│   │   ├── tester.py     # Test generation agent
│   │   └── orchestrator.py  # Multi-agent coordinator
│   ├── core/             # Engine modules
│   │   ├── llm.py        # OpenAI-compatible LLM client
│   │   ├── memory.py     # Shared memory for agents
│   │   ├── task.py       # Task definition & decomposition
│   │   └── pipeline.py   # DAG-based pipeline executor
│   ├── api/
│   │   └── routes.py     # FastAPI + WebSocket endpoints
│   ├── cli/
│   │   └── main.py       # CLI tool (Click + Rich)
│   ├── config.py         # Configuration management
│   └── main.py           # Server entry point
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   │   ├── Dashboard.tsx    # Main dashboard layout
│   │   │   ├── AgentCard.tsx    # Agent status card
│   │   │   ├── TaskFlow.tsx     # Pipeline flow visualization
│   │   │   ├── AgentChat.tsx    # Real-time communication log
│   │   │   └── TaskCreator.tsx  # Task submission form
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts  # WebSocket hook
│   │   └── types/
│   │       └── index.ts         # TypeScript types
│   ├── package.json
│   └── tsconfig.json
└── README.md
```

## 🔮 Use Cases

- **Automated Code Generation**: Describe a feature, get production-ready code with tests
- **Code Review Automation**: Multi-agent review catches issues single-agent tools miss
- **Legacy Code Migration**: Architect plans the migration, Coder implements, Reviewer validates
- **Documentation Generation**: Pipeline auto-generates docs from codebases
- **CI/CD Intelligence**: Integrate as a smart pipeline step for pre-merge validation

## 🤝 Contributing

Contributions are welcome! This project is part of the **Xiaomi MiMo Orbit Creator Incentive Program**.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License — free for personal and commercial use.

---

*Built with ❤️ for the MiMo Orbit 100 Trillion Token Creator Incentive Program*
