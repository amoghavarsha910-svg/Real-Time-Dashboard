import { create } from 'zustand';
import type { WSConnectionState, WSMessage, WSReading } from '@/types/ws';

const MAX_READINGS_PER_METRIC = 200;

interface WsState {
  connectionState: WSConnectionState;
  lastMessage: WSMessage | null;
  /** Ring buffer: last MAX_READINGS_PER_METRIC readings keyed by metric_id */
  readings: Record<string, WSReading[]>;
  /** Most recent reading for each metric_id */
  latestValues: Record<string, WSReading>;
  lastReceivedAt: string | null;

  setConnectionState: (state: WSConnectionState) => void;
  pushReading: (reading: WSReading) => void;
  setLastMessage: (msg: WSMessage) => void;
}

export const useWsStore = create<WsState>((set) => ({
  connectionState: 'DISCONNECTED',
  lastMessage: null,
  readings: {},
  latestValues: {},
  lastReceivedAt: null,

  setConnectionState: (connectionState) => set({ connectionState }),

  pushReading: (reading) =>
    set((state) => {
      const existing = state.readings[reading.metric_id] ?? [];
      const next =
        existing.length >= MAX_READINGS_PER_METRIC
          ? [...existing.slice(1), reading]
          : [...existing, reading];
      return {
        readings: { ...state.readings, [reading.metric_id]: next },
        latestValues: { ...state.latestValues, [reading.metric_id]: reading },
        lastReceivedAt: reading.timestamp,
      };
    }),

  setLastMessage: (lastMessage) => set({ lastMessage }),
}));
