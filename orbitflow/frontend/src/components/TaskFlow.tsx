import type { PipelineEvent } from "../types";

interface TaskFlowProps {
  events: PipelineEvent[];
}

const AGENT_ORDER = ["architect", "coder", "reviewer", "tester"];

export function TaskFlow({ events }: TaskFlowProps) {
  const agentStatuses: Record<string, "idle" | "working" | "done" | "failed"> = {
    architect: "idle",
    coder: "idle",
    reviewer: "idle",
    tester: "idle",
  };

  for (const e of events) {
    if (e.event_type === "agent_start") agentStatuses[e.agent] = "working";
    else if (e.event_type === "agent_end") agentStatuses[e.agent] = "done";
    else if (e.event_type === "log" && e.message.toLowerCase().includes("failed"))
      agentStatuses[e.agent] = "failed";
  }

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
