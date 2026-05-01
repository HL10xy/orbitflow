import { useEffect, useState } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { AgentCard } from "./AgentCard";
import { TaskFlow } from "./TaskFlow";
import { AgentChat } from "./AgentChat";
import { TaskCreator } from "./TaskCreator";
import type { Complexity, OrchestratorStatus } from "../types";

export function Dashboard() {
  const { connected, events, connect, disconnect, runTask } = useWebSocket();
  const [status, setStatus] = useState<OrchestratorStatus | null>(null);

  useEffect(() => {
    connect();
    fetch("/api/health")
      .then((r) => r.json())
      .then((d) => console.log("API:", d))
      .catch(() => {});
    fetch("/api/status")
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => {});
    return () => disconnect();
  }, []);

  const handleRun = (description: string, complexity: Complexity, title: string) => {
    runTask(description, complexity, title);
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>
          <span className="logo-icon">🚀</span> OrbitFlow
        </h1>
        <div className="header-info">
          <span className={`ws-indicator ${connected ? "connected" : "disconnected"}`}>
            {connected ? "Connected" : "Disconnected"}
          </span>
          {status && <span className="llm-info">Model: {status.llm}</span>}
        </div>
      </header>

      <div className="dashboard-grid">
        <aside className="sidebar">
          <TaskCreator onRun={handleRun} disabled={!connected} />

          <div className="agent-cards">
            <h3>Agents</h3>
            <AgentCard role="architect" events={events} />
            <AgentCard role="coder" events={events} />
            <AgentCard role="reviewer" events={events} />
            <AgentCard role="tester" events={events} />
          </div>
        </aside>

        <main className="main-content">
          <TaskFlow events={events} />
          <AgentChat events={events} />
        </main>
      </div>
    </div>
  );
}
