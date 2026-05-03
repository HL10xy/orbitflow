import React from "react";
import type { AgentRole, PipelineEvent } from "../types";

const AGENT_META: Record<AgentRole, { icon: string; color: string; label: string }> = {
  architect: { icon: "🏗️", color: "#f59e0b", label: "Architect" },
  coder: { icon: "💻", color: "#3b82f6", label: "Coder" },
  reviewer: { icon: "🔍", color: "#8b5cf6", label: "Reviewer" },
  tester: { icon: "🧪", color: "#10b981", label: "Tester" },
};

interface AgentCardProps {
  role: AgentRole;
  events: PipelineEvent[];
}

export const AgentCard = React.memo(function AgentCard({ role, events }: AgentCardProps) {
  const meta = AGENT_META[role] ?? { icon: "?", color: "#6b7280", label: role };
  const lastEvent = events[events.length - 1];

  let statusColor = "#6b7280";
  let statusText = "IDLE";
  if (lastEvent) {
    if (lastEvent.event_type === "agent_failed") {
      statusColor = "#ef4444";
      statusText = "FAILED";
    } else if (lastEvent.event_type === "agent_end") {
      statusColor = "#10b981";
      statusText = "DONE";
    } else if (lastEvent.event_type === "agent_start") {
      statusColor = "#f59e0b";
      statusText = "WORKING";
    }
  }

  const isActive = statusText === "WORKING";

  return (
    <div
      className="agent-card"
      style={{
        borderLeft: `4px solid ${meta.color}`,
        opacity: isActive ? 1 : 0.85,
        transition: "opacity 0.3s",
      }}
    >
      <div className="agent-card-header">
        <span className="agent-icon">{meta.icon}</span>
        <span className="agent-label">{meta.label}</span>
        <span className="agent-status" style={{ color: statusColor }}>
          {statusText}
        </span>
      </div>
      <div className="agent-card-body">
        {lastEvent ? (
          <p className="agent-last-msg">{lastEvent.message.slice(0, 120)}</p>
        ) : (
          <p className="agent-last-msg dim">Waiting for task assignment...</p>
        )}
      </div>
    </div>
  );
});
