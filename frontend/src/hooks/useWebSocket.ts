"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { getWebSocketUrl } from "@/lib/api";
import type { WSMessage } from "@/lib/types";

export function useWebSocket(jobId: string | null, enabled: boolean = true) {
  const [messages, setMessages] = useState<WSMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (!jobId || !enabled) return;

    const ws = new WebSocket(getWebSocketUrl(jobId));
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => {
      setIsConnected(false);
      if (enabled) {
        reconnectRef.current = setTimeout(connect, 3000);
      }
    };
    ws.onerror = () => ws.close();
    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);
        setMessages((prev) => [...prev, msg]);
      } catch {
        // ignore malformed messages
      }
    };
  }, [jobId, enabled]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const reset = useCallback(() => setMessages([]), []);

  return { messages, isConnected, reset };
}
