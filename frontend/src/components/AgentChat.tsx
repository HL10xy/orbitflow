import { useEffect, useRef } from "react";
import type { PipelineEvent } from "../types";

interface AgentChatProps {
  events: PipelineEvent[];
}

export function AgentChat({ events }: AgentChatProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  return (
    <div className="agent-chat">
      <h3>Agent Communication Log</h3>
      <div className="chat-log">
        {events.length === 0 && (
          <p className="chat-empty">
            Submit a task to see agents collaborate in real-time.
          </p>
        )}
        {events.map((e, i) => (
          <div key={`${e.timestamp}-${i}`} className={`chat-entry chat-${e.event_type}`}>
            <span className="chat-time">
              {new Date(e.timestamp * 1000).toLocaleTimeString()}
            </span>
            {e.agent && <span className="chat-agent">[{e.agent}]</span>}
            <span className="chat-msg">{e.message}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
