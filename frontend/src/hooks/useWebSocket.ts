import { useRef, useCallback, useState, useEffect } from "react";
import type { PipelineEvent } from "../types";

type WSCallback = (event: PipelineEvent) => void;

const MAX_EVENTS = 500;
const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000];

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const callbackRef = useRef<WSCallback | null>(null);
  const reconnectAttempt = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const manualClose = useRef(false);

  const doConnect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) return;

    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${location.host}/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      reconnectAttempt.current = 0;
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
      if (!manualClose.current) {
        const delay = RECONNECT_DELAYS[Math.min(reconnectAttempt.current, RECONNECT_DELAYS.length - 1)];
        reconnectAttempt.current++;
        reconnectTimer.current = setTimeout(doConnect, delay);
      }
    };

    ws.onerror = () => setConnected(false);

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        if (data.event_type === "done") return;
        setEvents((prev) => {
          const next = [...prev, data];
          return next.length > MAX_EVENTS ? next.slice(-MAX_EVENTS) : next;
        });
        callbackRef.current?.(data);
      } catch {
        // ignore parse errors
      }
    };
  }, []);

  const connect = useCallback(() => {
    manualClose.current = false;
    doConnect();
  }, [doConnect]);

  const disconnect = useCallback(() => {
    manualClose.current = true;
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      manualClose.current = true;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
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
