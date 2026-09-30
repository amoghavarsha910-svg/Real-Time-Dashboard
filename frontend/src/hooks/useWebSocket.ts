/**
 * Placeholder useWebSocket hook — full implementation in Phase 6.
 * Exporting the function signature here so imports resolve throughout Phase 1.
 */
import type { WSConnectionState, WSMessage } from '@/types/ws';

export interface UseWebSocketOptions {
  url?: string;
  enabled?: boolean;
}

export interface UseWebSocketReturn {
  connectionState: WSConnectionState;
  lastMessage: WSMessage | null;
  send: (data: string | object) => void;
  reconnect: () => void;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function useWebSocket(_options?: UseWebSocketOptions): UseWebSocketReturn {
  return {
    connectionState: 'DISCONNECTED',
    lastMessage: null,
    send: () => undefined,
    reconnect: () => undefined,
  };
}
