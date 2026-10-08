import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { PatientRegistrationPage } from './pages/PatientRegistrationPage';
import { QuestionnairePage } from './pages/QuestionnairePage';
import { MovementScreeningPage } from './pages/MovementScreeningPage';
import { ResultDashboardPage } from './pages/ResultDashboardPage';
import { PatientProfilePage } from './pages/PatientProfilePage';
import { PatientsListPage } from './pages/PatientsListPage';
import { ReportsPage } from './pages/ReportsPage';
import { QRAccessPage } from './pages/QRAccessPage';
import { LanguageProvider } from './utils/i18n';
import { Patient, QuestionnaireData, ScreeningRecord } from './types';
import { api } from './services/api';

export const App: React.FC = () => {
  // Check if opening direct QR access URL: /access/:token
  const initialQrToken = window.location.pathname.startsWith('/access/')
    ? window.location.pathname.replace('/access/', '').trim()
    : null;

  const [qrToken, setQrToken] = useState<string | null>(initialQrToken);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return !!localStorage.getItem('oasense_auth_token');
  });

  const [currentView, setCurrentView] = useState<string>(initialQrToken ? 'qr-access' : 'dashboard');

  // Screening Flow State
  const [activePatient, setActivePatient] = useState<Patient | null>(null);
  const [activeQuestionnaire, setActiveQuestionnaire] = useState<QuestionnaireData | null>(null);
  const [activeScreeningResult, setActiveScreeningResult] = useState<ScreeningRecord | null>(null);
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);

  // Session key to force fresh component mounting across new screenings
  const [screeningSessionKey, setScreeningSessionKey] = useState<number>(Date.now());

  const handleLogout = () => {
    api.logout();
    setIsAuthenticated(false);
  };

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
    setCurrentView('dashboard');
  };

  /**
   * Clears all active screening state across patient, questionnaire, and ML results
   * Generates a new screening session token/key and navigates to fresh Patient Registration.
   */
  const handleStartFreshScreening = () => {
    setActivePatient(null);
    setActiveQuestionnaire(null);
    setActiveScreeningResult(null);
    setSelectedPatientId(null);
    setScreeningSessionKey(Date.now());
    setCurrentView('register-patient');
  };

  /**
   * Starts a new screening specifically for an existing patient from Directory or Profile.
   * Clears old questionnaire, frames, and ML predictions while targeting the selected patient.
   */
  const handleStartExistingPatientScreening = (targetPatient: Patient) => {
    setActivePatient(targetPatient);
    setActiveQuestionnaire(null);
    setActiveScreeningResult(null);
    setScreeningSessionKey(Date.now());
    setCurrentView('questionnaire');
  };

  const handlePatientSaved = (newPatient: Patient, proceedToScreening: boolean) => {
    setActivePatient(newPatient);
    if (proceedToScreening) {
      setCurrentView('questionnaire');
    } else {
      setCurrentView('dashboard');
    }
  };

  const handleQuestionnaireCompleted = (data: QuestionnaireData) => {
    setActiveQuestionnaire(data);
    setCurrentView('movement-screening');
  };

  const handleScreeningFinished = (record: ScreeningRecord) => {
    setActiveScreeningResult(record);
    setCurrentView('screening-result');
  };

  const handleSelectPatientProfile = (patientId: number) => {
    setSelectedPatientId(patientId);
    setCurrentView('patient-profile');
  };

  const handleViewScreening = (record: ScreeningRecord) => {
    setActiveScreeningResult(record);
    setCurrentView('screening-result');
  };

  if (currentView === 'qr-access' && qrToken) {
    return (
      <LanguageProvider>
        <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900">
          <header className="bg-white border-b border-slate-200 py-3 px-6 shadow-xs flex items-center justify-between">
            <span className="font-black text-teal-700 tracking-tight text-lg">OA-Sense AI</span>
            <span className="text-xs text-slate-400 font-medium">Digital Patient Pass Portal</span>
          </header>
          <main className="flex-1">
            <QRAccessPage
              token={qrToken}
              onBack={() => {
                window.history.pushState({}, '', '/');
                setQrToken(null);
                setCurrentView('dashboard');
              }}
            />
          </main>
        </div>
      </LanguageProvider>
    );
  }

  if (!isAuthenticated) {
    return (
      <LanguageProvider>
        <LoginPage onLoginSuccess={handleLoginSuccess} />
      </LanguageProvider>
    );
  }

  return (
    <LanguageProvider>
      <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900">
        <Navbar
          currentView={currentView}
          setCurrentView={setCurrentView}
          onLogout={handleLogout}
          onStartNewScreening={handleStartFreshScreening}
        />

        <main className="flex-1">
          {currentView === 'dashboard' && (
            <DashboardPage
              onStartNewScreening={handleStartFreshScreening}
              onSelectPatient={handleSelectPatientProfile}
              onRegisterPatient={handleStartFreshScreening}
            />
          )}

          {currentView === 'patients' && (
            <PatientsListPage
              onSelectPatient={handleSelectPatientProfile}
              onRegisterPatient={handleStartFreshScreening}
              onStartScreening={(p) => handleStartExistingPatientScreening(p)}
            />
          )}

          {currentView === 'register-patient' && (
            <PatientRegistrationPage
              key={`reg-${screeningSessionKey}`}
              onPatientSaved={handlePatientSaved}
              onCancel={() => setCurrentView('dashboard')}
            />
          )}

          {currentView === 'questionnaire' && activePatient && (
            <QuestionnairePage
              key={`q-${screeningSessionKey}-${activePatient.id}`}
              patient={activePatient}
              onComplete={handleQuestionnaireCompleted}
              onBack={() => setCurrentView('dashboard')}
            />
          )}

          {currentView === 'movement-screening' && activePatient && activeQuestionnaire && (
            <MovementScreeningPage
              key={`mov-${screeningSessionKey}-${activePatient.id}`}
              patient={activePatient}
              questionnaire={activeQuestionnaire}
              onScreeningFinished={handleScreeningFinished}
              onBack={() => setCurrentView('questionnaire')}
            />
          )}

          {currentView === 'screening-result' && activeScreeningResult && (
            <ResultDashboardPage
              key={`res-${activeScreeningResult.id}`}
              screening={activeScreeningResult}
              onStartNewScreening={handleStartFreshScreening}
              onViewPatientProfile={handleSelectPatientProfile}
            />
          )}

          {currentView === 'patient-profile' && selectedPatientId && (
            <PatientProfilePage
              patientId={selectedPatientId}
              onBack={() => setCurrentView('dashboard')}
              onStartScreening={(p) => handleStartExistingPatientScreening(p)}
              onViewScreening={handleViewScreening}
            />
          )}

          {currentView === 'reports' && (
            <ReportsPage onSelectScreening={handleViewScreening} />
          )}
        </main>

        {/* Global Footer */}
        <footer className="bg-white border-t border-slate-200 py-6 px-4 text-center text-xs text-slate-400">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
            <p>
              <b>OA-Sense AI</b> — Community Outreach & Primary Care Early Osteoarthritis Risk Screening Prototype
            </p>
            <p className="text-slate-400">
              Not for clinical diagnosis • All rights reserved &copy; 2026
            </p>
          </div>
        </footer>
      </div>
    </LanguageProvider>
  );
};

export default App;
