import React, { useState } from 'react';
import { Activity, ShieldCheck, ArrowRight, Sparkles, Lock, Mail, AlertCircle } from 'lucide-react';
import { api } from '../services/api';
import { useTranslation } from '../utils/i18n';

interface LoginPageProps {
  onLoginSuccess: () => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const { t } = useTranslation();
  const [email, setEmail] = useState<string>('demo@oasense.ai');
  const [password, setPassword] = useState<string>('demo123');
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setErrorMessage(null);
    setLoading(true);

    try {
      await api.login(email, password);
      onLoginSuccess();
    } catch (err: any) {
      setErrorMessage(err.message || 'Login failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setEmail('demo@oasense.ai');
    setPassword('demo123');
    setErrorMessage(null);
    setLoading(true);

    try {
      await api.login('demo@oasense.ai', 'demo123');
      onLoginSuccess();
    } catch (err: any) {
      setErrorMessage(err.message || 'Demo login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[90vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 sm:p-10 rounded-3xl border border-slate-200 shadow-xl shadow-slate-200/50">
        {/* Brand Header */}
        <div className="text-center">
          <div className="mx-auto w-16 h-16 rounded-2xl bg-teal-600 flex items-center justify-center text-white shadow-lg shadow-teal-600/30 mb-4">
            <Activity className="w-9 h-9" />
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">OA-Sense <span className="text-teal-600">AI</span></h1>
          <p className="text-xs font-semibold text-teal-800 bg-teal-50 border border-teal-200 inline-block px-3 py-1 rounded-full mt-2">
            AI-Assisted Early Osteoarthritis Risk Screening System
          </p>
          <p className="text-xs text-slate-500 mt-2">
            Primary Healthcare & Community Outreach Screening Portal
          </p>
        </div>

        {/* Demo Credentials Alert Box */}
        <div className="bg-teal-50/70 border border-teal-200 rounded-2xl p-4 text-xs text-teal-900">
          <div className="flex items-center space-x-2 font-bold mb-1 text-teal-800">
            <Sparkles className="w-4 h-4 text-teal-600" />
            <span>Demonstration Account Access</span>
          </div>
          <p className="text-slate-600">Use pre-configured credentials or click Demo Login below:</p>
          <div className="mt-2 font-mono text-[11px] bg-white/80 p-2 rounded border border-teal-100 flex justify-between">
            <span>Email: <b>demo@oasense.ai</b></span>
            <span>Password: <b>demo123</b></span>
          </div>
        </div>

        {errorMessage && (
          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Staff Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500 text-sm font-medium"
                placeholder="healthcare.worker@oasense.ai"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">Secure Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500 text-sm font-medium"
                placeholder="••••••••"
              />
            </div>
          </div>

          <div className="space-y-2 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-sm flex items-center justify-center space-x-2 shadow-md shadow-teal-600/25 transition disabled:opacity-50"
            >
              <span>{loading ? 'Authenticating...' : 'Sign In to Portal'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              type="button"
              onClick={handleDemoLogin}
              disabled={loading}
              className="w-full py-2.5 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs flex items-center justify-center space-x-2 border border-slate-200 transition"
            >
              <Sparkles className="w-3.5 h-3.5 text-teal-600" />
              <span>One-Click Demo Login</span>
            </button>
          </div>
        </form>

        {/* Safety Disclaimer Footer */}
        <div className="pt-4 border-t border-slate-100 text-center">
          <p className="text-[11px] text-slate-400 leading-relaxed">
            <b>Notice:</b> This system is designed strictly for research, functional mobility evaluation, and preliminary screening. Never claim definitive clinical diagnosis without physical examination.
          </p>
        </div>
      </div>
    </div>
  );
};
