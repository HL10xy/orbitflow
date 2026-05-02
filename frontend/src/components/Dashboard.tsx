import { useEffect, useState, useCallback, useMemo } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { AgentCard } from "./AgentCard";
import { TaskFlow } from "./TaskFlow";
import { AgentChat } from "./AgentChat";
import { TaskCreator } from "./TaskCreator";
import { isOrchestratorStatus } from "../types";
import type { Complexity, OrchestratorStatus } from "../types";

export function Dashboard() {
  const { connected, events, connect, disconnect, runTask } = useWebSocket();
  const [status, setStatus] = useState<OrchestratorStatus | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const fetchStatus = useCallback(() => {
    fetch("/api/status")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        if (isOrchestratorStatus(data)) setStatus(data);
      })
      .catch((err) => {
        console.warn("Failed to fetch status:", err);
      });
  }, []);

  useEffect(() => {
    connect();
    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);
    return () => {
      clearInterval(interval);
      disconnect();
    };
  }, [connect, disconnect, fetchStatus]);

  // Track running state from events
  useEffect(() => {
    const hasStart = events.some((e) => e.event_type === "task_start");
    const hasEnd = events.some((e) => e.event_type === "task_end");
    setIsRunning(hasStart && !hasEnd);
  }, [events]);

  const handleRun = useCallback(
    (description: string, complexity: Complexity, title: string) => {
      runTask(description, complexity, title);
    },
    [runTask]
  );

  // Memoize per-agent event subsets to avoid re-filtering on every render
  const architectEvents = useMemo(
    () => events.filter((e) => e.agent === "architect"),
    [events]
  );
  const coderEvents = useMemo(
    () => events.filter((e) => e.agent === "coder"),
    [events]
  );
  const reviewerEvents = useMemo(
    () => events.filter((e) => e.agent === "reviewer"),
    [events]
  );
  const testerEvents = useMemo(
    () => events.filter((e) => e.agent === "tester"),
    [events]
  );

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
          <TaskCreator onRun={handleRun} disabled={!connected} isRunning={isRunning} />

          <div className="agent-cards">
            <h3>Agents</h3>
            <AgentCard role="architect" events={architectEvents} />
            <AgentCard role="coder" events={coderEvents} />
            <AgentCard role="reviewer" events={reviewerEvents} />
            <AgentCard role="tester" events={testerEvents} />
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
