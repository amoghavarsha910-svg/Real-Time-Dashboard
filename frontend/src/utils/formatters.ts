import { format, formatDistanceToNow, parseISO } from 'date-fns';

/**
 * Format a numeric value with optional unit label.
 * e.g. formatValue(42.5, '°C') → '42.50 °C'
 */
export function formatValue(value: number, unit?: string): string {
  const formatted = formatNumber(value, 2);
  return unit ? `${formatted} ${unit}` : formatted;
}

/**
 * Format an ISO timestamp to a human-readable date-time string.
 * e.g. '2024-06-01T14:32:00Z' → 'Jun 1, 2024 14:32:00'
 */
export function formatTimestamp(ts: string): string {
  try {
    return format(parseISO(ts), 'MMM d, yyyy HH:mm:ss');
  } catch {
    return ts;
  }
}

/**
 * Format an ISO timestamp as a relative time string.
 * e.g. '2 minutes ago'
 */
export function formatRelativeTime(ts: string): string {
  try {
    return formatDistanceToNow(parseISO(ts), { addSuffix: true });
  } catch {
    return ts;
  }
}

/**
 * Format a number with a fixed number of decimal places and thousands separators.
 */
export function formatNumber(n: number, decimals = 2): string {
  return n.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Map a metric status string to a Tailwind CSS text-color class.
 */
export function getStatusColor(status: string): string {
  switch (status) {
    case 'critical':
      return 'text-red-500';
    case 'warning':
      return 'text-yellow-500';
    case 'normal':
    default:
      return 'text-green-500';
  }
}

/**
 * Map a metric status string to a Tailwind CSS background-color class.
 */
export function getStatusBgColor(status: string): string {
  switch (status) {
    case 'critical':
      return 'bg-red-500/10 text-red-600 dark:text-red-400';
    case 'warning':
      return 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400';
    case 'normal':
    default:
      return 'bg-green-500/10 text-green-600 dark:text-green-400';
  }
}
