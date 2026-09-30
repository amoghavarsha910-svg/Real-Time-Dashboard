import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SettingsState {
  theme: 'light' | 'dark' | 'system';
  defaultTimeRange: string;
  refreshInterval: number;
  notificationsEnabled: boolean;

  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setDefaultTimeRange: (range: string) => void;
  setRefreshInterval: (n: number) => void;
  setNotificationsEnabled: (enabled: boolean) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      theme: 'system',
      defaultTimeRange: '1h',
      refreshInterval: 30,
      notificationsEnabled: true,

      setTheme: (theme) => set({ theme }),
      setDefaultTimeRange: (defaultTimeRange) => set({ defaultTimeRange }),
      setRefreshInterval: (refreshInterval) => set({ refreshInterval }),
      setNotificationsEnabled: (notificationsEnabled) => set({ notificationsEnabled }),
    }),
    { name: 'rtdd-settings' },
  ),
);
