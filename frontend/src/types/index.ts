export interface PipelineEvent {
  event_type: string;
  task_id: string;
  sub_task_id: string;
  agent: string;
  message: string;
  timestamp: number; // epoch seconds
}

export function isPipelineEvent(data: unknown): data is PipelineEvent {
  if (typeof data !== "object" || data === null) return false;
  const obj = data as Record<string, unknown>;
  return (
    typeof obj.event_type === "string" &&
    typeof obj.task_id === "string" &&
    typeof obj.sub_task_id === "string" &&
    typeof obj.agent === "string" &&
    typeof obj.message === "string" &&
    typeof obj.timestamp === "number"
  );
}

export interface SubTask {
  id: string;
  description: string;
  assigned_agent: string;
  status: string;
  result: string;
  dependencies: string[];
}

export interface Task {
  id: string;
  title: string;
  description: string;
  complexity: string;
  status: string;
  sub_tasks: SubTask[];
}

export interface MemorySnapshot {
  total_entries: number;
  entries: {
    id: number;
    role: string;
    content: string;
  }[];
}

export interface OrchestratorStatus {
  agents: string[];
  memory: MemorySnapshot;
  current_task: Task | null;
  llm: string;
}

export function isOrchestratorStatus(data: unknown): data is OrchestratorStatus {
  if (typeof data !== "object" || data === null) return false;
  const obj = data as Record<string, unknown>;
  if (!Array.isArray(obj.agents) || typeof obj.llm !== "string") return false;
  if (typeof obj.memory !== "object" || obj.memory === null) return false;
  const mem = obj.memory as Record<string, unknown>;
  if (typeof mem.total_entries !== "number" || !Array.isArray(mem.entries)) return false;
  if (obj.current_task !== null && typeof obj.current_task !== "object") return false;
  return true;
}

export type Complexity = "simple" | "moderate" | "complex" | "epic";
export type AgentRole = "architect" | "coder" | "reviewer" | "tester";
export type TaskStatus = "pending" | "in_progress" | "completed" | "failed";
export type EventType = "task_start" | "task_end" | "agent_start" | "agent_end" | "agent_failed" | "log";
