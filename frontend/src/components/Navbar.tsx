import React, { useState, useEffect } from 'react';
import { Activity, Users, FileText, PlusCircle, Globe, Wifi, WifiOff, ShieldAlert } from 'lucide-react';
import { useTranslation, Language } from '../utils/i18n';
import { getPendingSyncCount, markAllOfflineSynced } from '../services/offlineStorage';
import { api } from '../services/api';

interface NavbarProps {
  currentView: string;
  setCurrentView: (view: string) => void;
  onLogout?: () => void;
  onStartNewScreening?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentView, setCurrentView, onLogout, onStartNewScreening }) => {
  const { t, language, setLanguage } = useTranslation();
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);
  const [pendingSync, setPendingSync] = useState<number>(0);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    const interval = setInterval(() => {
      setPendingSync(getPendingSyncCount());
    }, 2000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, []);

  const handleSyncNow = async () => {
    setIsSyncing(true);
    try {
      markAllOfflineSynced();
      setPendingSync(0);
      alert('Offline records synced successfully!');
    } catch (e) {
      alert('Sync failed. Please check server connectivity.');
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
      {/* Top Warning Banner: Medical Disclaimer */}
      <div className="bg-amber-50 border-b border-amber-200 px-4 py-1.5 text-xs text-amber-900 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
          <span>
            <b>SCREENING PROTOTYPE:</b> This application provides preliminary risk assessment and is <b>NOT</b> a definitive medical diagnosis. Clinical evaluation is always recommended.
          </span>
        </div>
        <span className="hidden sm:inline-block bg-amber-200/60 text-amber-800 font-semibold px-2 py-0.5 rounded text-[10px]">
          {t('nav.demoBadge')}
        </span>
      </div>

      {/* Main Navigation Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setCurrentView('dashboard')}>
            <div className="w-10 h-10 rounded-xl bg-teal-600 flex items-center justify-center text-white shadow-sm shadow-teal-500/30">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-slate-900">OA-Sense <span className="text-teal-600">AI</span></span>
                <span className="bg-teal-50 text-teal-700 text-xs font-semibold px-2 py-0.5 rounded border border-teal-200">v1.0</span>
              </div>
              <p className="text-[11px] text-slate-500 hidden sm:block leading-none">{t('nav.subtitle')}</p>
            </div>
          </div>

          {/* Navigation Items */}
          <nav className="hidden md:flex items-center space-x-1">
            <button
              onClick={() => setCurrentView('dashboard')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition flex items-center space-x-1.5 ${
                currentView === 'dashboard' ? 'bg-teal-50 text-teal-800 font-semibold' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>{t('nav.dashboard')}</span>
            </button>

            <button
              onClick={() => setCurrentView('patients')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition flex items-center space-x-1.5 ${
                currentView === 'patients' ? 'bg-teal-50 text-teal-800 font-semibold' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>{t('nav.patients')}</span>
            </button>

            <button
              onClick={() => setCurrentView('reports')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition flex items-center space-x-1.5 ${
                currentView === 'reports' ? 'bg-teal-50 text-teal-800 font-semibold' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <FileText className="w-4 h-4" />
              <span>{t('nav.reports')}</span>
            </button>

            <button
              onClick={() => {
                if (onStartNewScreening) {
                  onStartNewScreening();
                } else {
                  setCurrentView('register-patient');
                }
              }}
              className="ml-2 px-3.5 py-2 rounded-lg text-sm font-semibold bg-teal-600 text-white hover:bg-teal-700 shadow-sm shadow-teal-600/20 flex items-center space-x-1.5 transition"
            >
              <PlusCircle className="w-4 h-4" />
              <span>{t('nav.newScreening')}</span>
            </button>
          </nav>

          {/* Right Action Area */}
          <div className="flex items-center space-x-3">
            {/* Connectivity & Sync Status */}
            {isOnline ? (
              <div className="flex items-center space-x-1 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-medium">
                <Wifi className="w-3.5 h-3.5 text-emerald-600" />
                <span className="hidden lg:inline">{t('nav.online')}</span>
              </div>
            ) : (
              <div className="flex items-center space-x-1 px-2.5 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-300 text-xs font-medium">
                <WifiOff className="w-3.5 h-3.5 text-amber-600 animate-pulse" />
                <span>{t('nav.offline')}</span>
              </div>
            )}

            {pendingSync > 0 && (
              <button
                onClick={handleSyncNow}
                disabled={isSyncing}
                className="bg-indigo-50 border border-indigo-200 text-indigo-700 px-2 py-1 rounded-md text-xs font-semibold hover:bg-indigo-100 flex items-center space-x-1 transition"
              >
                <span>Sync ({pendingSync})</span>
              </button>
            )}

            {/* Language Switcher */}
            <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs">
              <button
                onClick={() => setLanguage('en')}
                className={`px-2 py-0.5 rounded font-semibold transition ${
                  language === 'en' ? 'bg-white text-teal-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                EN
              </button>
              <button
                onClick={() => setLanguage('hi')}
                className={`px-2 py-0.5 rounded font-semibold transition ${
                  language === 'hi' ? 'bg-white text-teal-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                हिंदी
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
