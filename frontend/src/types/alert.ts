export type AlertSeverity = 'info' | 'warning' | 'critical';
export type AlertOperator = 'gt' | 'lt' | 'gte' | 'lte' | 'eq' | 'neq';

export interface AlertRule {
  id: string;
  name: string;
  metric_id: string;
  operator: AlertOperator;
  threshold: number;
  severity: AlertSeverity;
  duration_seconds: number;
  is_enabled: boolean;
  owner_id: string;
  created_at: string;
  metric?: { name: string; display_name: string; unit: string };
}

export interface AlertEvent {
  id: string;
  rule_id: string;
  triggered_value: number;
  triggered_at: string;
  resolved_at?: string;
  message?: string;
  rule?: AlertRule;
}
