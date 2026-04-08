import { useEffect, useRef, useState, useCallback } from 'react';
import type { WsMessage, ConnectionState } from '../types/live';

const WS_URL = 'ws://localhost:8000/ws';
const MAX_RETRIES = 8;
const BASE_DELAY_MS = 1000;

interface UseWebSocketOptions {
  onMessage: (msg: WsMessage) => void;
}

export function useWebSocket({ onMessage }: UseWebSocketOptions) {
  const [state, setState] = useState<ConnectionState>('connecting');
  const wsRef     = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const timerRef  = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    setState('connecting');

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      setState('connected');
      retriesRef.current = 0;
      // heartbeat ping every 20 s to keep connection alive
      const ping = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send('ping');
      }, 20_000);
      ws.onclose = () => {
        clearInterval(ping);
        handleDisconnect();
      };
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;
      try {
        const msg = JSON.parse(event.data) as WsMessage;
        onMessage(msg);
      } catch { /* ignore malformed */ }
    };

    ws.onerror = () => {
      setState('error');
    };

    // Fallback close handler before open
    ws.onclose = () => handleDisconnect();
  }, [onMessage]);

  function handleDisconnect() {
    if (!mountedRef.current) return;
    setState('disconnected');
    if (retriesRef.current >= MAX_RETRIES) return;
    const delay = BASE_DELAY_MS * Math.pow(2, retriesRef.current);
    retriesRef.current += 1;
    timerRef.current = setTimeout(connect, delay);
  }

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { state };
}
