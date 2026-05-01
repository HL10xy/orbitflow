import { useRef, useCallback, useState } from "react";
import type { PipelineEvent, OrchestratorStatus } from "../types";

type WSCallback = (event: PipelineEvent) => void;

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const callbackRef = useRef<WSCallback | null>(null);

  const connect = useCallback(() => {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${location.host}/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        if (data.event_type === "done") return;
        setEvents((prev) => [...prev, data]);
        callbackRef.current?.(data);
      } catch {
        // ignore parse errors
      }
    };

    return () => ws.close();
  }, []);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, []);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const onEvent = useCallback((cb: WSCallback) => {
    callbackRef.current = cb;
  }, []);

  const runTask = useCallback(
    (description: string, complexity: string, title = "") => {
      setEvents([]);
      send({ action: "run", description, complexity, title });
    },
    [send]
  );

  const clearEvents = useCallback(() => setEvents([]), []);

  return { connected, events, connect, disconnect, send, onEvent, runTask, clearEvents };
}
