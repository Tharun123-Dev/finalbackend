import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import rolesApi from '@/services/rolesApi';

interface RegisterResponse {
  token?: string;
}

export default function RegisterUser() {
  const [tenantName, setTenantName] = useState('');
  const [tenantCode, setTenantCode] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setMessage(null);
    setError(null);
    setLoading(true);

    const payload = {
      tenantName,
      tenantCode: tenantCode || null,
      firstName,
      lastName,
      email,
      password,
    };

    try {
      const response = await rolesApi.post<RegisterResponse>('/auth/register', payload);
      const token = response.data.token;
      if (token) {
        localStorage.setItem('token', token);
        setMessage('Tenant Admin Registration Successful! Token stored in localStorage.');
      } else {
        setMessage('Tenant Admin Registered successfully!');
      }
      // Reset form
      setTenantName('');
      setTenantCode('');
      setFirstName('');
      setLastName('');
      setEmail('');
      setPassword('');
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { message?: string } } };
      setError(axiosError.response?.data?.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4 font-sans text-slate-200">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
        {/* Decorative background glow */}
        <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-cyan-900/20 to-transparent pointer-events-none" />

        <div className="text-center mb-8 relative z-10">
          <h2 className="text-2xl font-bold text-slate-50">Register Tenant & Admin User</h2>
          <p className="text-slate-400 mt-2">Initialize workspace and administrative accounts</p>
        </div>

        {message && <div className="bg-emerald-500/10 text-emerald-500 p-3 rounded-xl mb-6 border border-emerald-500/20 text-sm relative z-10">{message}</div>}
        {error && <div className="bg-rose-500/10 text-rose-400 p-3 rounded-xl mb-6 border border-rose-500/20 text-sm relative z-10">{error}</div>}

        <form onSubmit={handleRegister} className="space-y-4 relative z-10">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Tenant Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Acme Corp"
                className="w-full bg-slate-950/50 border border-slate-700 text-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 transition-all placeholder:text-slate-600 text-sm"
                value={tenantName}
                onChange={(e) => setTenantName(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Tenant Code (Optional)</label>
              <input
                type="text"
                placeholder="e.g. ACM"
                className="w-full bg-slate-950/50 border border-slate-700 text-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 transition-all placeholder:text-slate-600 text-sm"
                value={tenantCode}
                onChange={(e) => setTenantCode(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">First Name</label>
              <input
                type="text"
                required
                placeholder="First Name"
                className="w-full bg-slate-950/50 border border-slate-700 text-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 transition-all placeholder:text-slate-600 text-sm"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Last Name</label>
              <input
                type="text"
                required
                placeholder="Last Name"
                className="w-full bg-slate-950/50 border border-slate-700 text-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 transition-all placeholder:text-slate-600 text-sm"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Admin Email</label>
            <input
              type="email"
              required
              placeholder="admin@company.com"
              className="w-full bg-slate-950/50 border border-slate-700 text-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 transition-all placeholder:text-slate-600 text-sm"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Admin Password</label>
            <input
              type="password"
              required
              placeholder="Password"
              className="w-full bg-slate-950/50 border border-slate-700 text-slate-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 transition-all placeholder:text-slate-600 text-sm"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-white font-semibold py-3 px-4 rounded-xl shadow-lg shadow-cyan-500/20 transition-all active:scale-95 flex items-center justify-center disabled:opacity-70 disabled:cursor-not-allowed text-sm mt-4"
          >
            {loading ? 'Registering...' : 'Register'}
          </button>
        </form>

        <div className="text-center mt-6 relative z-10 text-sm">
          <span className="text-slate-400">
            Need to sign in? <Link to="/login" className="text-cyan-400 hover:text-cyan-300 font-medium transition-colors">Sign In</Link>
          </span>
        </div>
      </div>
    </div>
  );
}


