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
import { LanguageProvider } from './utils/i18n';
import { Patient, QuestionnaireData, ScreeningRecord } from './types';
import { api } from './services/api';

export const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return !!localStorage.getItem('oasense_auth_token');
  });

  const [currentView, setCurrentView] = useState<string>('dashboard');

  // Screening Flow State
  const [activePatient, setActivePatient] = useState<Patient | null>(null);
  const [activeQuestionnaire, setActiveQuestionnaire] = useState<QuestionnaireData | null>(null);
  const [activeScreeningResult, setActiveScreeningResult] = useState<ScreeningRecord | null>(null);
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);

  const handleLogout = () => {
    api.logout();
    setIsAuthenticated(false);
  };

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
    setCurrentView('dashboard');
  };

  // Workflow transitions
  const handleStartNewScreening = async (targetPatient?: Patient) => {
    if (targetPatient) {
      setActivePatient(targetPatient);
      setCurrentView('questionnaire');
    } else {
      // If no patient selected, pick the first existing patient or prompt registration
      try {
        const patients = await api.getPatients();
        if (patients.length > 0) {
          setActivePatient(patients[0]);
          setCurrentView('questionnaire');
        } else {
          setCurrentView('register-patient');
        }
      } catch {
        setCurrentView('register-patient');
      }
    }
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
        />

        <main className="flex-1">
          {currentView === 'dashboard' && (
            <DashboardPage
              onStartNewScreening={() => handleStartNewScreening()}
              onSelectPatient={handleSelectPatientProfile}
              onRegisterPatient={() => setCurrentView('register-patient')}
            />
          )}

          {currentView === 'patients' && (
            <PatientsListPage
              onSelectPatient={handleSelectPatientProfile}
              onRegisterPatient={() => setCurrentView('register-patient')}
              onStartScreening={(p) => handleStartNewScreening(p)}
            />
          )}

          {currentView === 'register-patient' && (
            <PatientRegistrationPage
              onPatientSaved={handlePatientSaved}
              onCancel={() => setCurrentView('dashboard')}
            />
          )}

          {currentView === 'questionnaire' && activePatient && (
            <QuestionnairePage
              patient={activePatient}
              onComplete={handleQuestionnaireCompleted}
              onBack={() => setCurrentView('dashboard')}
            />
          )}

          {currentView === 'movement-screening' && activePatient && activeQuestionnaire && (
            <MovementScreeningPage
              patient={activePatient}
              questionnaire={activeQuestionnaire}
              onScreeningFinished={handleScreeningFinished}
              onBack={() => setCurrentView('questionnaire')}
            />
          )}

          {currentView === 'screening-result' && activeScreeningResult && (
            <ResultDashboardPage
              screening={activeScreeningResult}
              onStartNewScreening={() => handleStartNewScreening()}
              onViewPatientProfile={handleSelectPatientProfile}
            />
          )}

          {currentView === 'patient-profile' && selectedPatientId && (
            <PatientProfilePage
              patientId={selectedPatientId}
              onBack={() => setCurrentView('dashboard')}
              onStartScreening={(p) => handleStartNewScreening(p)}
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
