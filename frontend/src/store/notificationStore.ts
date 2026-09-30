import { create } from 'zustand';
import type { Notification } from '@/types/notification';
import type { AlertSeverity } from '@/types/alert';

interface Toast {
  id: string;
  title: string;
  body?: string;
  severity: AlertSeverity | 'info';
}

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  toasts: Toast[];

  addNotification: (n: Notification) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  pushToast: (t: Omit<Toast, 'id'>) => void;
  dismissToast: (id: string) => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [],
  unreadCount: 0,
  toasts: [],

  addNotification: (n) =>
    set((state) => ({
      notifications: [n, ...state.notifications],
      unreadCount: state.unreadCount + (n.is_read ? 0 : 1),
    })),

  markRead: (id) =>
    set((state) => {
      const notifications = state.notifications.map((n) =>
        n.id === id ? { ...n, is_read: true } : n,
      );
      const unreadCount = notifications.filter((n) => !n.is_read).length;
      return { notifications, unreadCount };
    }),

  markAllRead: () =>
    set((state) => ({
      notifications: state.notifications.map((n) => ({ ...n, is_read: true })),
      unreadCount: 0,
    })),

  pushToast: (t) =>
    set((state) => ({
      toasts: [...state.toasts, { ...t, id: crypto.randomUUID() }],
    })),

  dismissToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
}));
