import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import rolesApi from '@/services/rolesApi';

export default function Signup() {
  const navigate = useNavigate();
  
  const [tenantName, setTenantName] = useState('');
  const [adminFirstName, setAdminFirstName] = useState('');
  const [adminLastName, setAdminLastName] = useState('');
  const [adminEmail, setAdminEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSignup = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setMessage(null);
    setError(null);
    setLoading(true);

    const payload = {
      tenantName,
      adminFirstName,
      adminLastName,
      adminEmail,
      phone,
      adminPassword,
    };

    try {
      await rolesApi.post('/auth/register-company', payload);
      setMessage('Company registered successfully! Your 15-Day Trial has started.');
      setTimeout(() => navigate('/login'), 2500);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { message?: string } } };
      setError(axiosError.response?.data?.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4 font-sans text-foreground">
      <div className="w-full max-w-lg bg-card border border-border rounded-2xl p-8 shadow-2xl relative overflow-hidden">
        {/* Decorative background glow */}
        <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-cyan-900/20 to-transparent pointer-events-none" />

        <div className="text-center mb-8 relative z-10">
          <span className="inline-flex items-center rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-400 border border-cyan-500/20 mb-3 tracking-wider">
            15-DAY FREE TRIAL
          </span>
          <h2 className="text-2xl font-bold text-foreground">Register Your Company</h2>
          <p className="text-muted-foreground mt-2">Create your workspace and start your trial today</p>
        </div>

        {message && <div className="bg-emerald-500/10 text-emerald-500 p-3 rounded-xl mb-6 border border-emerald-500/20 text-sm relative z-10">{message}</div>}
        {error && <div className="bg-rose-500/10 text-rose-400 p-3 rounded-xl mb-6 border border-rose-500/20 text-sm relative z-10">{error}</div>}

        <form onSubmit={handleSignup} className="space-y-4 relative z-10">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Company Name</label>
            <input
              type="text"
              required
              placeholder="e.g. Acme Corp"
              className="w-full bg-background border border-border text-foreground rounded-xl px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 transition-all placeholder:text-muted-foreground text-sm"
              value={tenantName}
              onChange={(e) => setTenantName(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">First Name</label>
              <input
                type="text"
                required
                placeholder="John"
                className="w-full bg-background border border-border text-foreground rounded-xl px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 transition-all placeholder:text-muted-foreground text-sm"
                value={adminFirstName}
                onChange={(e) => setAdminFirstName(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Last Name</label>
              <input
                type="text"
                required
                placeholder="Doe"
                className="w-full bg-background border border-border text-foreground rounded-xl px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 transition-all placeholder:text-muted-foreground text-sm"
                value={adminLastName}
                onChange={(e) => setAdminLastName(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Work Email</label>
              <input
                type="email"
                required
                placeholder="john@company.com"
                className="w-full bg-background border border-border text-foreground rounded-xl px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 transition-all placeholder:text-muted-foreground text-sm"
                value={adminEmail}
                onChange={(e) => setAdminEmail(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">Phone Number</label>
              <input
                type="text"
                required
                placeholder="+1 234 567 8900"
                className="w-full bg-background border border-border text-foreground rounded-xl px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 transition-all placeholder:text-muted-foreground text-sm"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">Password</label>
            <input
              type="password"
              required
              placeholder="••••••••"
              minLength={6}
              className="w-full bg-background border border-border text-foreground rounded-xl px-4 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500 focus:border-cyan-500 transition-all placeholder:text-muted-foreground text-sm"
              value={adminPassword}
              onChange={(e) => setAdminPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-white font-semibold py-3 px-4 rounded-xl shadow-lg shadow-cyan-500/20 transition-all active:scale-95 flex items-center justify-center disabled:opacity-70 disabled:cursor-not-allowed text-sm mt-4"
          >
            {loading ? 'Setting up your workspace...' : 'Start Free Trial'}
          </button>
        </form>

        <div className="text-center mt-6 relative z-10 text-sm">
          <span className="text-muted-foreground">
            Already have an account? <Link to="/login" className="text-cyan-400 hover:text-cyan-300 font-medium transition-colors">Sign In</Link>
          </span>
        </div>
      </div>
    </div>
  );
}


