export type NotificationType = 'alert' | 'system' | 'report' | 'connection';

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  body?: string;
  type: NotificationType;
  is_read: boolean;
  reference_id?: string;
  created_at: string;
}
