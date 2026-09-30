export type MetricStatus = 'normal' | 'warning' | 'critical';

export interface MetricDefinition {
  id: string;
  name: string;
  display_name: string;
  unit: string;
  min_value?: number;
  max_value?: number;
  category?: string;
}

export interface DataSource {
  id: string;
  name: string;
  source_type: string;
  is_enabled: boolean;
  last_seen_at?: string;
  config?: Record<string, unknown>;
  created_at: string;
}

export interface DataReading {
  id: number;
  metric_id: string;
  source_id: string;
  value: number;
  status: MetricStatus;
  timestamp: string;
  metric?: MetricDefinition;
  source?: DataSource;
}

export interface DashboardSummary {
  total_readings_24h: number;
  active_sources: number;
  active_alerts: number;
  data_rate: number;
  system_status: 'normal' | 'warning' | 'critical';
  avg_values: Record<string, number>;
}
