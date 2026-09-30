export type WSMessageType =
  | 'reading'
  | 'alert'
  | 'notification'
  | 'source_status'
  | 'system'
  | 'ping';

export interface WSMessage<T = unknown> {
  type: WSMessageType;
  timestamp: string;
  data: T;
}

export interface WSReading {
  metric: string;
  metric_id: string;
  value: number;
  unit: string;
  source: string;
  source_id: string;
  status: 'normal' | 'warning' | 'critical';
  timestamp: string;
}

export type WSConnectionState = 'CONNECTING' | 'CONNECTED' | 'RECONNECTING' | 'DISCONNECTED';
