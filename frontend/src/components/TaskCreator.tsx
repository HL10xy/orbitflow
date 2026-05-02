import { useState } from "react";
import type { Complexity } from "../types";

interface TaskCreatorProps {
  onRun: (description: string, complexity: Complexity, title: string) => void;
  disabled: boolean;
  isRunning: boolean;
}

const COMPLEXITY_OPTIONS: { value: Complexity; label: string; desc: string }[] = [
  { value: "simple", label: "Simple", desc: "1-2 agents, linear flow" },
  { value: "moderate", label: "Moderate", desc: "3-4 agents, review & test" },
  { value: "complex", label: "Complex", desc: "All agents, iterative refinement" },
  { value: "epic", label: "Epic", desc: "Full pipeline, parallel sub-tasks" },
];

export function TaskCreator({ onRun, disabled, isRunning }: TaskCreatorProps) {
  const [description, setDescription] = useState("");
  const [title, setTitle] = useState("");
  const [complexity, setComplexity] = useState<Complexity>("moderate");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;
    onRun(description.trim(), complexity, title.trim());
    setDescription("");
    setTitle("");
    setComplexity("moderate");
  };

  const buttonText = isRunning ? "Running..." : disabled ? "Disconnected" : "Run Pipeline";

  return (
    <form className="task-creator" onSubmit={handleSubmit}>
      <h3>New Task</h3>
      <input
        type="text"
        className="input"
        placeholder="Task title (optional)"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <textarea
        className="textarea"
        placeholder="Describe your software engineering task...&#10;e.g. Build a REST API for user authentication with JWT tokens"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        rows={4}
        maxLength={10000}
      />
      <div className="complexity-selector" role="radiogroup" aria-label="Task complexity">
        {COMPLEXITY_OPTIONS.map((opt) => (
          <label
            key={opt.value}
            className={`complexity-option ${complexity === opt.value ? "selected" : ""}`}
            role="radio"
            aria-checked={complexity === opt.value}
          >
            <input
              type="radio"
              name="complexity"
              value={opt.value}
              checked={complexity === opt.value}
              onChange={() => setComplexity(opt.value)}
            />
            <span className="complexity-label">{opt.label}</span>
            <span className="complexity-desc">{opt.desc}</span>
          </label>
        ))}
      </div>
      <button type="submit" className="btn-run" disabled={isRunning || disabled || !description.trim()}>
        {buttonText}
      </button>
    </form>
  );
}
