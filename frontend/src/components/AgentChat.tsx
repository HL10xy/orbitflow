import { useEffect, useRef, useState } from "react";
import type { PipelineEvent } from "../types";

const VISIBLE_LIMIT = 100;

interface AgentChatProps {
  events: PipelineEvent[];
}

export function AgentChat({ events }: AgentChatProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [showAll, setShowAll] = useState(false);

  // Reset showAll when events are cleared (new task)
  useEffect(() => {
    if (events.length === 0) setShowAll(false);
  }, [events.length]);

  const visibleEvents = showAll ? events : events.slice(-VISIBLE_LIMIT);
  const hiddenCount = events.length - visibleEvents.length;

  // Smart auto-scroll: only when user is near the bottom
  const logRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = logRef.current;
    if (!el) return;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 150;
    if (isNearBottom) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [events.length]);

  return (
    <div className="agent-chat">
      <h3>Agent Communication Log</h3>
      <div className="chat-log" role="log" aria-live="polite" ref={logRef}>
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
        {showAll && events.length > VISIBLE_LIMIT && (
          <button className="chat-show-more" onClick={() => setShowAll(false)}>
            Show latest {VISIBLE_LIMIT} only
          </button>
        )}
        {visibleEvents.map((e, i) => (
          <div key={`${e.timestamp}-${e.agent}-${e.sub_task_id}-${i}`} className={`chat-entry chat-${e.event_type}`}>
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
