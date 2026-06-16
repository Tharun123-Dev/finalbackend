import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Landmark, UserCheck, ShieldAlert } from 'lucide-react';
import rolesApi from '@/services/rolesApi';
import EntityFormPage from '@/components/shared/EntityFormPage';

interface CreateTenantProps {
  onClose?: () => void;
  onSuccess?: () => void;
}

export default function CreateTenant({ onClose, onSuccess }: CreateTenantProps = {}) {
  const navigate = useNavigate();
  const [tenantName, setTenantName] = useState('');
  const [tenantCode, setTenantCode] = useState('');
  const [adminFirstName, setAdminFirstName] = useState('');
  const [adminLastName, setAdminLastName] = useState('');
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPassword, setAdminPassword] = useState('');

  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 4000);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const payload = {
      tenantName,
      tenantCode: tenantCode || null,
      adminFirstName,
      adminLastName,
      adminEmail,
      adminPassword,
    };

    try {
      await rolesApi.post('/tenants', payload);
      showToast('success', 'Tenant and admin profile created successfully!');
      if (onSuccess) {
        setTimeout(onSuccess, 1000);
      } else {
        setTimeout(() => {
          navigate('/tenants');
        }, 1500);
      }
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { message?: string } | string }; message?: string };
      let errorMsg = 'Failed to create tenant workspace.';
      if (axiosError.response) {
        if (typeof axiosError.response.data === 'object' && axiosError.response.data?.message) {
          errorMsg = axiosError.response.data.message;
        } else if (typeof axiosError.response.data === 'string') {
          errorMsg = axiosError.response.data;
        }
      } else if (axiosError.message) {
        errorMsg = axiosError.message;
      }
      showToast('error', errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={onClose ? "w-full" : "max-w-4xl mx-auto space-y-6"}>
      {/* Toast Alert */}
      {toast && (
        <div
          className={`fixed top-4 right-4 z-[9999] px-4 py-3 rounded-xl shadow-lg border text-sm transition-all duration-300 ${
            toast.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
              : 'bg-rose-500/10 border-rose-500/20 text-rose-455'
          }`}
          role="alert"
        >
          {toast.msg}
        </div>
      )}

      {/* Onboarding Header Banner */}
      {!onClose && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Landmark className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100 tracking-tight">Onboard New Tenant Workspace</h2>
            <p className="text-slate-400 text-xs">
              Provision a new logically isolated database instance and map the initial Super Admin profile.
            </p>
          </div>
        </div>
      )}

      <EntityFormPage
        title="Create Tenant Workspace"
        onSubmit={handleSubmit}
        loading={loading}
        isModal={Boolean(onClose)}
        onBack={onClose}
      >
        <div className="space-y-6">
          {/* Section: Company Profile details */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
              <Landmark className="w-4 h-4" /> Workspace Details
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Tenant/Company Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Acme Corporation"
                  className="w-full bg-background border border-slate-850 text-slate-200 text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  value={tenantName}
                  onChange={(e) => setTenantName(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Tenant Code (Identifier)
                </label>
                <input
                  type="text"
                  placeholder="e.g. ACM"
                  className="w-full bg-background border border-slate-850 text-slate-200 text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  value={tenantCode}
                  onChange={(e) => setTenantCode(e.target.value.toUpperCase())}
                />
                <span className="text-[10px] text-slate-500 block mt-1">
                  Optional. Short uppercase string used as routing header code.
                </span>
              </div>
            </div>
          </div>

          <hr className="border-slate-850" />

          {/* Section: Admin User Account credentials */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
              <UserCheck className="w-4 h-4" /> Tenant Administrator Profile
            </h3>
            
            <div className="bg-amber-500/5 border border-amber-500/10 p-4 rounded-xl text-amber-400/90 text-xs flex gap-3 mb-4">
              <ShieldAlert className="w-5 h-5 flex-shrink-0" />
              <div>
                <span className="font-bold">System Privilege Notice:</span> This administrator account will be granted full `SUPER_ADMIN` system credentials for the new isolated database tenant.
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Admin First Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="Rahul"
                  className="w-full bg-background border border-slate-850 text-slate-200 text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  value={adminFirstName}
                  onChange={(e) => setAdminFirstName(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Admin Last Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="Sharma"
                  className="w-full bg-background border border-slate-850 text-slate-200 text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  value={adminLastName}
                  onChange={(e) => setAdminLastName(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Admin Email Address <span className="text-rose-500">*</span>
                </label>
                <input
                  type="email"
                  required
                  placeholder="admin@acme.com"
                  className="w-full bg-background border border-slate-850 text-slate-200 text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  value={adminEmail}
                  onChange={(e) => setAdminEmail(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Admin Password <span className="text-rose-500">*</span>
                </label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  className="w-full bg-background border border-slate-850 text-slate-200 text-sm rounded-lg px-3 py-2.5 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  value={adminPassword}
                  onChange={(e) => setAdminPassword(e.target.value)}
                />
              </div>
            </div>
          </div>
        </div>
      </EntityFormPage>
    </div>
  );
}


