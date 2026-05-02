export interface PipelineEvent {
  event_type: string;
  task_id: string;
  sub_task_id: string;
  agent: string;
  message: string;
  timestamp: number; // epoch seconds
}

export function isPipelineEvent(data: unknown): data is PipelineEvent {
  return (
    typeof data === "object" && data !== null &&
    "event_type" in data && typeof (data as any).event_type === "string"
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
  return (
    typeof data === "object" && data !== null &&
    "agents" in data && Array.isArray((data as any).agents) &&
    "memory" in data &&
    "llm" in data
  );
}

export type Complexity = "simple" | "moderate" | "complex" | "epic";
