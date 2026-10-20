import { useEffect, useRef, useState } from "react";
import { WS_BASE, getToken } from "./api";

/** Opens a WebSocket for live events and reconnects automatically if it drops. */
export function useLiveEvents(enabled, onEvent) {
  const [connected, setConnected] = useState(false);
  const handler = useRef(onEvent);
  handler.current = onEvent;

  useEffect(() => {
    if (!enabled) return undefined;
    let socket;
    let retryTimer;
    let closedByUs = false;

    const connect = () => {
      socket = new WebSocket(`${WS_BASE}/ws?token=${encodeURIComponent(getToken() || "")}`);
      socket.onopen = () => setConnected(true);
      socket.onmessage = (message) => {
        try { handler.current(JSON.parse(message.data)); } catch { /* ignore malformed events */ }
      };
      socket.onclose = () => {
        setConnected(false);
        if (!closedByUs) retryTimer = setTimeout(connect, 3000);
      };
    };
    connect();
    return () => {
      closedByUs = true;
      clearTimeout(retryTimer);
      socket?.close();
    };
  }, [enabled]);

  return connected;
}
