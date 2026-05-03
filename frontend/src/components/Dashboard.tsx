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
  const [statusError, setStatusError] = useState<string | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);

  const fetchStatus = useCallback(() => {
    fetch("/api/status")
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        if (isOrchestratorStatus(data)) {
          setStatus(data);
          setStatusError(null);
        }
      })
      .catch((err) => {
        setStatusError("Failed to connect to server");
        console.warn("Failed to fetch status:", err);
      })
      .finally(() => setStatusLoading(false));
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

  // Track running state from events; reset on disconnect
  useEffect(() => {
    if (!connected) {
      setIsRunning(false);
      return;
    }
    const hasStart = events.some((e) => e.event_type === "task_start");
    const hasEnd = events.some((e) => e.event_type === "task_end");
    setIsRunning(hasStart && !hasEnd);
  }, [events, connected]);

  const handleRun = useCallback(
    (description: string, complexity: Complexity, title: string) => {
      runTask(description, complexity, title);
    },
    [runTask]
  );

  // Single-pass bucket: partition events by agent in one traversal
  const eventsByAgent = useMemo(() => {
    const buckets: Record<string, typeof events> = { architect: [], coder: [], reviewer: [], tester: [] };
    for (const e of events) {
      if (e.agent in buckets) buckets[e.agent].push(e);
    }
    return buckets;
  }, [events]);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>
          <span className="logo-icon">🚀</span> OrbitFlow
        </h1>
        <div className="header-info">
          <span className={`ws-indicator ${connected ? "connected" : "disconnected"}`} role="status">
            {connected ? "Connected" : "Disconnected"}
          </span>
          {statusLoading && <span className="llm-info">Loading...</span>}
          {!statusLoading && status && <span className="llm-info">Model: {status.llm}</span>}
        </div>
      </header>

      {statusError && (
        <div className="status-error-banner" role="alert">
          {statusError}
        </div>
      )}

      <div className="dashboard-grid">
        <aside className="sidebar">
          <TaskCreator onRun={handleRun} disabled={!connected} isRunning={isRunning} />

          <div className="agent-cards">
            <h3>Agents</h3>
            <AgentCard role="architect" events={eventsByAgent.architect} />
            <AgentCard role="coder" events={eventsByAgent.coder} />
            <AgentCard role="reviewer" events={eventsByAgent.reviewer} />
            <AgentCard role="tester" events={eventsByAgent.tester} />
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
