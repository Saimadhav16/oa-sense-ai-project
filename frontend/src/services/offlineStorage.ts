import { ScreeningRecord, Patient } from '../types';

const OFFLINE_SCREENINGS_KEY = 'oasense_offline_screenings_queue';
const OFFLINE_PATIENTS_KEY = 'oasense_offline_patients_queue';

export const getOfflineScreenings = (): any[] => {
  try {
    const raw = localStorage.getItem(OFFLINE_SCREENINGS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
};

export const saveOfflineScreening = (screening: any): void => {
  const current = getOfflineScreenings();
  const entry = {
    ...screening,
    local_id: 'offline_' + Date.now(),
    sync_status: 'pending_sync',
    created_at: new Date().toISOString()
  };
  current.push(entry);
  localStorage.setItem(OFFLINE_SCREENINGS_KEY, JSON.stringify(current));
};

export const getPendingSyncCount = (): number => {
  const queue = getOfflineScreenings();
  return queue.filter(q => q.sync_status === 'pending_sync').length;
};

export const clearSyncedOfflineScreenings = (): void => {
  const current = getOfflineScreenings();
  const pending = current.filter(q => q.sync_status === 'pending_sync');
  localStorage.setItem(OFFLINE_SCREENINGS_KEY, JSON.stringify(pending));
};

export const markAllOfflineSynced = (): void => {
  localStorage.removeItem(OFFLINE_SCREENINGS_KEY);
};
