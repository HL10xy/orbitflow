# OrbitFlow — Multi-Agent Software Engineering Framework

**A production-grade multi-agent collaboration framework that orchestrates specialized AI agents to automate complex software engineering workflows.**

---

## Overview

OrbitFlow implements a **multi-agent pipeline architecture** where four specialized AI agents — **Architect, Coder, Reviewer, and Tester** — collaborate through a shared memory space to solve complex software engineering tasks end-to-end.

```
┌──────────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Architect   │───▶│  Coder   │───▶│ Reviewer │───▶│  Tester  │
│  Design &    │    │ Implement│    │ Review & │    │ Test &   │
│  Planning    │    │ Core Logic│    │ Validate │    │ Verify   │
└──────────────┘    └──────────┘    └──────────┘    └──────────┘
        │                  │               │               │
        └──────────────────┴───────────────┴───────────────┘
                           Shared Memory
```

Tasks are decomposed into dependency-ordered sub-tasks. Independent sub-tasks execute **in parallel** via asyncio DAG scheduling. If a sub-task fails, all downstream dependents are automatically skipped.

## Architecture

| Component | Technology | Description |
|-----------|-----------|-------------|
| **Agent Engine** | Python 3.10+ | Role-based agents with configurable system prompts and context hints |
| **Orchestrator** | Python (asyncio) | Task decomposition, dependency resolution, concurrent-safe execution |
| **Shared Memory** | Python (OrderedDict) | Inter-agent communication with FIFO eviction |
| **LLM Client** | httpx (persistent) | OpenAI-compatible API client with connection pooling and automatic retry |
| **API Server** | FastAPI + WebSocket | REST API + real-time streaming with optional API key auth |
| **CLI Tool** | Click + Rich | Terminal-based pipeline runner with live status |
| **Dashboard** | React 18 + TypeScript | Real-time visualization with auto-reconnect and performance optimizations |
| **Pipeline** | Python (asyncio) | Parallel DAG execution with failure propagation |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- An OpenAI-compatible API key (MiMo, OpenAI, or any compatible provider)

### 1. Clone & Setup Backend

```bash
git clone https://github.com/HL10xy/orbitflow.git
cd orbitflow/backend

pip install -r requirements.txt

# Configure your LLM provider
export LLM_BASE_URL="https://api.xiaomimimo.com/v1"
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

## Configuration

All configuration is via environment variables (or `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BASE_URL` | `https://api.xiaomimimo.com/v1` | OpenAI-compatible API endpoint |
| `LLM_API_KEY` | *(required)* | API key for the LLM provider |
| `LLM_MODEL` | `mimo-v2.5-pro` | Model name |
| `ORBITFLOW_API_KEY` | *(empty)* | API key for OrbitFlow's own endpoints (optional; if set, `/config/llm` and WebSocket require it) |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:8000` | Comma-separated allowed CORS origins |
| `ORBITFLOW_DEBUG` | `false` | Enable auto-reload for development |

## Supported LLM Providers

OrbitFlow uses an OpenAI-compatible API interface:

- **Xiaomi MiMo** — `https://api.xiaomimimo.com/v1`
- **OpenAI** — `https://api.openai.com/v1`
- **Any OpenAI-compatible endpoint** (vLLM, Ollama, LiteLLM, etc.)

The LLM client reuses HTTP connections across calls and automatically retries on transient errors (429, 500, 502, 503) with exponential backoff.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/status` | Orchestrator status and memory snapshot |
| `POST` | `/task/run` | Run a task (non-streaming) |
| `POST` | `/config/llm` | Update LLM configuration (requires API key if configured) |
| `WS` | `/ws` | Real-time agent collaboration stream |

### WebSocket Protocol

```json
// Send a task
{"action": "run", "description": "Build a todo API", "complexity": "moderate"}

// Receive real-time events
{"event_type": "agent_start", "agent": "architect", "message": "..."}
{"event_type": "agent_end", "agent": "architect"}
{"event_type": "task_end", "message": "Task completed: ..."}
```

If `ORBITFLOW_API_KEY` is set, pass it as a query parameter: `ws://host/ws?token=your-key`

## Task Complexity Levels

| Level | Agents | Flow | Description |
|-------|--------|------|-------------|
| **Simple** | 2 | Linear | Architect → Coder |
| **Moderate** | 4 | Sequential + Parallel | Architect → Coder → Reviewer + Tester (parallel) |
| **Complex** | 4 | DAG | Architect → Coder(A) + Coder(B) → Reviewer(A+B) → Tester |
| **Epic** | 4 | Full DAG | Same as Complex with more sub-tasks |

Independent sub-tasks run concurrently. If any sub-task fails, downstream dependents are skipped automatically.

## Project Structure

```
orbitflow/
├── backend/
│   ├── agents/           # Specialized AI agents
│   │   ├── base.py       # Base agent with common run() logic
│   │   ├── architect.py  # Architecture design (role + context hint)
│   │   ├── coder.py      # Code generation
│   │   ├── reviewer.py   # Code review
│   │   ├── tester.py     # Test generation
│   │   └── orchestrator.py  # Multi-agent coordinator
│   ├── core/             # Engine modules
│   │   ├── llm.py        # LLM client (persistent connection, retry)
│   │   ├── memory.py     # Shared memory for agents
│   │   ├── task.py       # Task definition & decomposition
│   │   └── pipeline.py   # Parallel DAG executor with failure propagation
│   ├── api/
│   │   └── routes.py     # FastAPI + WebSocket endpoints
│   ├── cli/
│   │   └── main.py       # CLI tool (Click + Rich)
│   ├── config.py         # Configuration management
│   └── main.py           # Server entry point
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   │   ├── Dashboard.tsx    # Main layout with memoized event routing
│   │   │   ├── AgentCard.tsx    # Memoized agent status card
│   │   │   ├── TaskFlow.tsx     # Pipeline flow visualization
│   │   │   ├── AgentChat.tsx    # Windowed event log
│   │   │   └── TaskCreator.tsx  # Accessible task form
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts  # WebSocket with auto-reconnect
│   │   └── types/
│   │       └── index.ts         # Types + runtime type guards
│   ├── package.json
│   └── tsconfig.json
└── README.md
```

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License — free for personal and commercial use.
