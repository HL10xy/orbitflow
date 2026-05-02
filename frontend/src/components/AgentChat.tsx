import { useEffect, useRef, useState } from "react";
import type { PipelineEvent } from "../types";

const VISIBLE_LIMIT = 100;

interface AgentChatProps {
  events: PipelineEvent[];
}

export function AgentChat({ events }: AgentChatProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [showAll, setShowAll] = useState(false);

  const visibleEvents = showAll ? events : events.slice(-VISIBLE_LIMIT);
  const hiddenCount = events.length - visibleEvents.length;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  return (
    <div className="agent-chat">
      <h3>Agent Communication Log</h3>
      <div className="chat-log" role="log" aria-live="polite">
        {events.length === 0 && (
          <p className="chat-empty">
            Submit a task to see agents collaborate in real-time.
          </p>
        )}
        {hiddenCount > 0 && !showAll && (
          <button className="chat-show-more" onClick={() => setShowAll(true)}>
            Show {hiddenCount} earlier events
          </button>
        )}
        {visibleEvents.map((e, i) => (
          <div key={`${e.timestamp}-${e.agent}-${i}`} className={`chat-entry chat-${e.event_type}`}>
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
