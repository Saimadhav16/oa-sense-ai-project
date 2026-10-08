import {
  Patient,
  ScreeningRecord,
  DashboardStats,
  QuestionnaireData,
  MovementSummary,
  PredictionResult
} from '../types';
import { saveOfflineScreening } from './offlineStorage';

// Determine API Base URL dynamically:
// 1. Explicit VITE_API_BASE_URL environment variable if provided
// 2. If opened from mobile/LAN (non-localhost/127.0.0.1), use the same host with backend port 8000
// 3. Fallback to http://127.0.0.1:8000 for local development
const resolveApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_BASE_URL as string;
  if (envUrl && envUrl.trim()) {
    return envUrl.trim().replace(/\/$/, '');
  }
  if (typeof window !== 'undefined' && window.location) {
    const { hostname, protocol } = window.location;
    if (hostname && hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return `${protocol}//${hostname}:8000`;
    }
  }
  return 'http://127.0.0.1:8000';
};

export const API_BASE_URL = resolveApiBaseUrl();

const getAuthHeaders = (): HeadersInit => {
  const token = localStorage.getItem('oasense_auth_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
};

export const api = {
  // Authentication
  async login(email: string, password: string) {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    localStorage.setItem('oasense_auth_token', data.access_token);
    localStorage.setItem('oasense_user_name', data.user_name);
    localStorage.setItem('oasense_user_email', data.user_email);
    return data;
  },

  logout() {
    localStorage.removeItem('oasense_auth_token');
    localStorage.removeItem('oasense_user_name');
    localStorage.removeItem('oasense_user_email');
  },

  // Dashboard Stats
  async getDashboardStats(): Promise<DashboardStats> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/dashboard/statistics`, {
        headers: getAuthHeaders()
      });
      if (!res.ok) throw new Error('Failed to load stats');
      return await res.json();
    } catch (e) {
      // Return sensible offline demo fallback
      return {
        total_patients: 3,
        screenings_today: 1,
        high_risk_cases: 1,
        moderate_risk_cases: 1,
        low_risk_cases: 1,
        risk_distribution: {
          'Low Risk': 1,
          'Moderate Risk': 1,
          'High Risk': 1
        },
        recent_activity: []
      };
    }
  },

  // Patients
  async getPatients(search?: string, riskFilter?: string): Promise<Patient[]> {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (riskFilter && riskFilter !== 'all') params.append('risk_filter', riskFilter);

    const res = await fetch(`${API_BASE_URL}/api/patients?${params.toString()}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Failed to fetch patients');
    return await res.json();
  },

  async getPatientById(id: number): Promise<{ patient: Patient; screenings: any[]; trajectory?: any; qr_passes?: any[] }> {
    const res = await fetch(`${API_BASE_URL}/api/patients/${id}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Patient not found');
    return await res.json();
  },

  async createPatient(patient: Partial<Patient>): Promise<Patient> {
    const res = await fetch(`${API_BASE_URL}/api/patients`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(patient)
    });
    if (!res.ok) throw new Error('Failed to create patient');
    return await res.json();
  },

  // Screenings & Analysis
  async analyzeQuestionnaire(q: QuestionnaireData) {
    const res = await fetch(`${API_BASE_URL}/api/analysis/questionnaire`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(q)
    });
    return await res.json();
  },

  async predictRisk(payload: {
    age: number;
    activity_level: string;
    joint_injury: number;
    family_history: number;
    questionnaire: QuestionnaireData;
    movement: MovementSummary;
  }): Promise<PredictionResult> {
    const res = await fetch(`${API_BASE_URL}/api/analysis/predict`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Prediction request failed');
    return await res.json();
  },

  async submitScreening(screeningPayload: {
    patient_id: number;
    questionnaire: QuestionnaireData;
    movement: MovementSummary;
    notes?: string;
  }): Promise<ScreeningRecord> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/screenings`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(screeningPayload)
      });
      if (!res.ok) throw new Error('Failed to submit screening to server');
      return await res.json();
    } catch (err) {
      console.warn('Network unreachable, queuing screening for offline sync:', err);
      // Offline fallback: save locally
      saveOfflineScreening(screeningPayload);
      throw new Error('OFFLINE_SAVED');
    }
  },

  async getScreenings(patientId?: number, riskLevel?: string): Promise<ScreeningRecord[]> {
    const params = new URLSearchParams();
    if (patientId) params.append('patient_id', patientId.toString());
    if (riskLevel && riskLevel !== 'all') params.append('risk_level', riskLevel);

    const res = await fetch(`${API_BASE_URL}/api/screenings?${params.toString()}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Failed to fetch screenings');
    return await res.json();
  },

  async getScreeningById(id: number) {
    const res = await fetch(`${API_BASE_URL}/api/screenings/${id}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Screening not found');
    return await res.json();
  },

  // Reports
  async generateReport(screeningId: number): Promise<{ report_id: number; file_name: string; download_url: string }> {
    const res = await fetch(`${API_BASE_URL}/api/reports/generate`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ screening_id: screeningId })
    });
    if (!res.ok) throw new Error('Failed to generate PDF report');
    return await res.json();
  },

  getReportDownloadUrl(reportId: number): string {
    return `${API_BASE_URL}/api/reports/${reportId}`;
  },

  async updatePatient(id: number, data: Partial<Patient>): Promise<Patient> {
    const res = await fetch(`${API_BASE_URL}/api/patients/${id}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('Failed to update patient record');
    return await res.json();
  },

  async getPatientTrajectory(id: number): Promise<{ patient_id: number; trajectory: any }> {
    const res = await fetch(`${API_BASE_URL}/api/patients/${id}/trajectory`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Failed to load patient trajectory');
    return await res.json();
  },

  // Secure QR Access Management
  async generatePatientQR(patientId: number, expiresInHours: number = 72): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/patients/${patientId}/qr`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ expires_in_hours: expiresInHours })
    });
    if (!res.ok) throw new Error('Failed to generate secure QR token');
    return await res.json();
  },

  async revokePatientQR(qrId: number): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/patients/qr/${qrId}/revoke`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Failed to revoke QR access pass');
    return await res.json();
  },

  async accessPatientByQR(token: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/access/qr/${token}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Invalid or expired QR token' }));
      throw new Error(err.detail || 'Access denied');
    }
    return await res.json();
  },

  // Audit Logs & Sync Queue Observability
  async getAuditLogs(action?: string, limit: number = 30): Promise<any[]> {
    const params = new URLSearchParams();
    if (action) params.append('action', action);
    params.append('limit', limit.toString());
    const res = await fetch(`${API_BASE_URL}/api/audit-logs?${params.toString()}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) return [];
    return await res.json();
  },

  async getSyncQueueStatus(): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/sync/queue`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Failed to fetch sync queue status');
    return await res.json();
  },

  async retryFailedSync(): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/sync/retry`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error('Failed to retry sync queue');
    return await res.json();
  },

  // Offline Sync
  async syncOfflineBatch(batch: any[]) {
    const res = await fetch(`${API_BASE_URL}/api/screenings/sync`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(batch)
    });
    return await res.json();
  }
};
