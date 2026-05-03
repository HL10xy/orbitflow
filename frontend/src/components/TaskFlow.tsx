import { useMemo } from "react";
import type { AgentRole, PipelineEvent } from "../types";

interface TaskFlowProps {
  events: PipelineEvent[];
}

const AGENT_ORDER: AgentRole[] = ["architect", "coder", "reviewer", "tester"];

export function TaskFlow({ events }: TaskFlowProps) {
  const agentStatuses = useMemo(() => {
    const statuses: Record<AgentRole, "idle" | "working" | "done" | "failed"> = {
      architect: "idle",
      coder: "idle",
      reviewer: "idle",
      tester: "idle",
    };
    for (const e of events) {
      const agent = e.agent as AgentRole;
      if (!(agent in statuses)) continue;
      if (e.event_type === "agent_start") statuses[agent] = "working";
      else if (e.event_type === "agent_end") statuses[agent] = "done";
      else if (e.event_type === "agent_failed") statuses[agent] = "failed";
    }
    return statuses;
  }, [events]);

  return (
    <div className="task-flow">
      <h3>Pipeline Flow</h3>
      <div className="flow-line">
        {AGENT_ORDER.map((role, i) => (
          <div key={role} className="flow-node-wrapper">
            <div className={`flow-node ${agentStatuses[role]}`}>
              <span className="flow-dot" />
            </div>
            <span className="flow-label">{role}</span>
            {i < AGENT_ORDER.length - 1 && <div className="flow-connector" />}
          </div>
        ))}
      </div>
    </div>
  );
}
