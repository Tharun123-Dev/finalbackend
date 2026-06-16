import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Landmark, Layers, Users, ShieldAlert, BarChart3, Database, Mail, Phone, Calendar, Play, X } from 'lucide-react';
import rolesApi from '@/services/rolesApi';

interface Tenant {
  id: number;
  name: string;
  code: string;
  dbName: string;
  adminEmail: string | null;
  active: boolean;
  status?: string;
  superAdminName?: string;
  phone?: string;
  subscriptionType?: string;
  subscriptionStartDate?: string;
  subscriptionEndDate?: string;
}

interface TenantModule {
  moduleName: string;
  active: boolean;
  amount: number | null;
  paymentMethod: string;
  specialRequirements: string | null;
  extraCharges: number | null;
}

interface TenantDetailsProps {
  tenantId?: number | null;
  onClose?: () => void;
}

export default function TenantDetails({ tenantId, onClose }: TenantDetailsProps = {}) {
  const { id: paramId } = useParams<{ id: string }>();
  const activeId = tenantId !== undefined ? tenantId : (paramId ? Number(paramId) : null);
  const navigate = useNavigate();
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [modules, setModules] = useState<TenantModule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTenantData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [tenantRes, modulesRes] = await Promise.all([
          rolesApi.get<Tenant[]>('/tenants'),
          rolesApi.get<TenantModule[]>(`/tenants/${activeId}/modules`),
        ]);

        const found = (tenantRes.data || []).find((t) => t.id === Number(activeId));
        if (found) {
          setTenant(found);
        } else {
          setError('Tenant registry entry not found.');
        }

        if (modulesRes.data) {
          setModules(modulesRes.data);
        }
      } catch (err: unknown) {
        const axiosError = err as { message?: string };
        setError(axiosError.message || 'Failed to query tenant profiles.');
      } finally {
        setLoading(false);
      }
    };

    if (activeId) {
      fetchTenantData();
    }
  }, [activeId]);

  if (loading) {
    return (
      <div className="flex min-h-[300px] flex-col items-center justify-center gap-2">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin text-primary" />
        <div className="text-sm text-slate-400">Fetching workspace profile details...</div>
      </div>
    );
  }

  if (error || !tenant) {
    return (
      <div className={onClose ? "w-full space-y-4" : "max-w-4xl mx-auto space-y-4"}>
        {!onClose && (
          <button
            type="button"
            onClick={() => navigate('/tenants')}
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Tenants
          </button>
        )}
        <div className="bg-rose-500/10 border border-rose-500/20 text-rose-455 p-6 rounded-2xl text-center">
          <ShieldAlert className="w-8 h-8 mx-auto mb-2" />
          <h4 className="font-bold">Error Displaying Profile</h4>
          <p className="text-xs mt-1">{error || 'Tenant workspace details could not be parsed.'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={onClose ? "w-full" : "max-w-5xl mx-auto space-y-6"}>
      {/* Back navigation */}
      {!onClose && (
        <button
          type="button"
          onClick={() => navigate('/tenants')}
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Tenants
        </button>
      )}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 rounded-full blur-2xl" />
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <Landmark className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-bold text-slate-100 tracking-tight">{tenant.name}</h1>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${
                    tenant.active
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : 'bg-rose-500/10 text-rose-455 border-rose-500/20'
                  }`}
                >
                  {tenant.active ? 'Active' : 'Disabled'}
                </span>
              </div>
              <p className="text-slate-400 text-xs mt-1 font-mono">
                Code ID: <span className="text-cyan-400 font-bold">{tenant.code}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">Account status:</span>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
              {tenant.status || 'ACTIVE'}
            </span>
          </div>
        </div>

        <hr className="border-slate-800/80 my-5" />

        {/* Contact info grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
          <div className="flex items-center gap-2 text-slate-400">
            <Database className="w-4 h-4 text-slate-500 flex-shrink-0" />
            <div>
              <span className="block text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Isolated Database</span>
              <span className="text-slate-300 font-mono">{tenant.dbName}</span>
            </div>
          </div>

          <div className="flex items-center gap-2 text-slate-400">
            <Mail className="w-4 h-4 text-slate-500 flex-shrink-0" />
            <div>
              <span className="block text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Admin Email</span>
              <span className="text-slate-300">{tenant.adminEmail || 'N/A'}</span>
            </div>
          </div>

          <div className="flex items-center gap-2 text-slate-400">
            <Phone className="w-4 h-4 text-slate-500 flex-shrink-0" />
            <div>
              <span className="block text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Phone Contact</span>
              <span className="text-slate-300">{tenant.phone || 'N/A'}</span>
            </div>
          </div>

          <div className="flex items-center gap-2 text-slate-400">
            <Calendar className="w-4 h-4 text-slate-500 flex-shrink-0" />
            <div>
              <span className="block text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Subscription Term</span>
              <span className="text-slate-300">
                {tenant.subscriptionStartDate || '-'} to {tenant.subscriptionEndDate || '-'}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Configured modules section */}
        <div className="md:col-span-2 space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
              <Layers className="w-4 h-4" /> Subscription Module Mappings
            </h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              Note: <strong>SYSTEM_ADMIN</strong> and <strong>EMPLOYEE</strong> are core service containers automatically provisioned on launch to guarantee baseline portal operation.
            </p>

            <hr className="border-slate-800" />

            <div className="space-y-3">
              {modules.length > 0 ? (
                modules.map((m) => (
                  <div
                    key={m.moduleName}
                    className="flex items-center justify-between p-3.5 rounded-xl bg-slate-950/40 border border-slate-850/60"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-6 h-6 rounded-full flex items-center justify-center border ${
                          m.active
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-slate-800/40 text-slate-600 border-slate-800'
                        }`}
                      >
                        {m.active ? <Play className="w-3 h-3 fill-emerald-400/20" /> : <X className="w-3.5 h-3.5" />}
                      </div>
                      <span className={`text-sm font-bold ${m.active ? 'text-slate-200' : 'text-slate-500 line-through'}`}>
                        {m.moduleName}
                      </span>
                    </div>

                    {m.active && (
                      <div className="flex items-center gap-4 text-xs text-slate-400">
                        {m.amount !== null && (
                          <span>
                            License Fee: <strong className="text-slate-200">${m.amount}</strong>
                          </span>
                        )}
                        <span>
                          Method: <strong className="text-slate-300">{m.paymentMethod}</strong>
                        </span>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-slate-500 text-xs py-2">No subscription modules detected.</div>
              )}
            </div>
          </div>
        </div>

        {/* Resources container block */}
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
              <BarChart3 className="w-4 h-4" /> Live Resource Load
            </h3>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-slate-950/40 border border-slate-850/60 rounded-xl text-center">
                <Users className="w-5 h-5 mx-auto mb-1 text-slate-500" />
                <span className="block text-[10px] text-slate-500 uppercase tracking-wider font-semibold">User Seats</span>
                <span className="text-sm font-bold text-slate-300">—</span>
              </div>

              <div className="p-3 bg-slate-950/40 border border-slate-850/60 rounded-xl text-center">
                <Database className="w-5 h-5 mx-auto mb-1 text-slate-500" />
                <span className="block text-[10px] text-slate-500 uppercase tracking-wider font-semibold">DB Usage</span>
                <span className="text-sm font-bold text-slate-300">—</span>
              </div>
            </div>

            <div className="bg-slate-950/30 border border-slate-850 p-4 rounded-xl space-y-2.5 text-xs text-slate-400">
              <div className="flex justify-between">
                <span>Billing Status:</span>
                <span className="text-slate-300 font-semibold">—</span>
              </div>
              <div className="flex justify-between">
                <span>API Calls:</span>
                <span className="text-slate-300 font-semibold">—</span>
              </div>
              <div className="flex justify-between">
                <span>Data Logs:</span>
                <span className="text-slate-300 font-semibold">—</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


