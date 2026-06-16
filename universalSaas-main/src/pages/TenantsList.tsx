import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Layers, RefreshCw, Sliders, ToggleLeft, ToggleRight, Building, X, ShieldAlert } from 'lucide-react';
import rolesApi from '@/services/rolesApi';
import EntityListPage from '@/components/shared/EntityListPage';
import Modal from '@/components/ui/Modal';
import CreateTenant from '@/pages/CreateTenant';
import TenantDetails from '@/pages/TenantDetails';
import { usePermissions } from '@/auth/usePermissions';

interface Tenant {
  id: number;
  name: string;
  code: string;
  dbName: string;
  adminEmail: string | null;
  active: boolean;
  status?: string;
}

interface TenantModule {
  id?: number;
  moduleName: string;
  active: boolean;
  amount: number | null;
  paymentMethod: string;
  specialRequirements: string | null;
  extraCharges: number | null;
}

const ALL_MODULES = ['CRM', 'HRMS', 'VENDOR'];

export default function TenantsList() {
  const { hasPermission } = usePermissions();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  // Module configuration modal states
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [moduleDetails, setModuleDetails] = useState<Record<string, TenantModule>>({});
  const [initialActiveModules, setInitialActiveModules] = useState<string[]>([]);
  const [savingModules, setSavingModules] = useState(false);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [viewingTenantId, setViewingTenantId] = useState<number | null>(null);

  const showToast = useCallback((type: 'success' | 'error', msg: string) => {
    setToast({ type, msg });
    setTimeout(() => setToast(null), 4000);
  }, []);

  const fetchTenants = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const response = await rolesApi.get<Tenant[]>('/tenants', { signal });
      setTenants(response.data);
    } catch (err: unknown) {
      const axiosError = err as { name?: string; response?: { data?: { message?: string } }; message?: string };
      if (axiosError.name === 'CanceledError') return;
      setError(axiosError.response?.data?.message || axiosError.message || 'Failed to fetch system tenants.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const ctrl = new AbortController();
    fetchTenants(ctrl.signal);
    return () => ctrl.abort();
  }, [fetchTenants]);

  const handleToggleStatus = async (tenant: Tenant) => {
    const action = tenant.active ? 'disable' : 'enable';
    try {
      await rolesApi.put(`/tenants/${tenant.id}/${action}`);
      setTenants((prev) =>
        prev.map((t) => (t.id === tenant.id ? { ...t, active: !tenant.active } : t))
      );
      showToast('success', `Tenant "${tenant.name}" has been ${action}d successfully.`);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { message?: string } }; message?: string };
      showToast('error', axiosError.response?.data?.message || axiosError.message || 'Failed to switch tenant status.');
    }
  };

  const handleManageModules = async (tenant: Tenant) => {
    setSelectedTenant(tenant);
    try {
      const response = await rolesApi.get<TenantModule[]>(`/tenants/${tenant.id}/modules`);
      const data = response.data || [];
      const activeNames = data.filter((m) => m.active).map((m) => m.moduleName);
      setInitialActiveModules(activeNames);

      const details: Record<string, TenantModule> = {};
      ALL_MODULES.forEach((m) => {
        details[m] = {
          moduleName: m,
          active: false,
          amount: null,
          paymentMethod: 'Card',
          specialRequirements: '',
          extraCharges: null,
        };
      });

      data.forEach((m) => {
        if (details[m.moduleName]) {
          details[m.moduleName] = {
            ...m,
            specialRequirements: m.specialRequirements || '',
          };
        }
      });

      setModuleDetails(details);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { message?: string } }; message?: string };
      showToast('error', 'Failed to fetch modules: ' + (axiosError.response?.data?.message || axiosError.message));
    }
  };

  const handleModuleDetailChange = (
    moduleName: string,
    field: keyof TenantModule,
    value: string | number | boolean | null
  ) => {
    setModuleDetails((prev) => ({
      ...prev,
      [moduleName]: {
        ...prev[moduleName],
        [field]: value,
      },
    }));
  };

  const saveModules = async () => {
    if (!selectedTenant) return;
    setSavingModules(true);
    try {
      const promises: Promise<unknown>[] = [];

      for (const moduleName of ALL_MODULES) {
        const detail = moduleDetails[moduleName];
        const wasActive = initialActiveModules.includes(moduleName);

        if (detail.active) {
          const payload = {
            amount: detail.amount !== null && !isNaN(Number(detail.amount)) ? Number(detail.amount) : null,
            paymentMethod: detail.paymentMethod,
            specialRequirements: detail.specialRequirements || null,
            extraCharges: detail.extraCharges !== null && !isNaN(Number(detail.extraCharges)) ? Number(detail.extraCharges) : null,
          };
          promises.push(rolesApi.put(`/tenants/${selectedTenant.id}/modules/${moduleName}/enable`, payload));
        } else if (wasActive) {
          promises.push(rolesApi.put(`/tenants/${selectedTenant.id}/modules/${moduleName}/disable`));
        }
      }

      await Promise.all(promises);
      showToast('success', `Modules config saved successfully for "${selectedTenant.name}".`);
      setSelectedTenant(null);
      fetchTenants();
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { message?: string } }; message?: string };
      showToast('error', 'Failed to save modules: ' + (axiosError.response?.data?.message || axiosError.message));
    } finally {
      setSavingModules(false);
    }
  };

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return tenants;
    return tenants.filter((t) =>
      [t.name, t.code, t.adminEmail, t.dbName]
        .filter(Boolean)
        .some((v) => v!.toLowerCase().includes(q))
    );
  }, [tenants, search]);

  return (
    <div className="space-y-6">
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

      <EntityListPage
        title="Tenants"
        description="System Master Administration workspace for setting up clients, managing databases, and managing active license modules."
        addLabel={hasPermission('TENANT_CREATE') ? "Create Tenant" : undefined}
        onAdd={() => setIsCreateOpen(true)}
        searchValue={search}
        onSearchChange={setSearch}
        loading={loading}
        error={error}
        totalCount={!loading ? filtered.length : undefined}
        headerActions={
          <button
            type="button"
            className="inline-flex items-center gap-1.5 justify-center rounded-md border border-border bg-muted hover:bg-muted/80 h-9 px-3 text-sm font-semibold text-foreground active:scale-95 transition-all"
            onClick={() => fetchTenants()}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="border-b border-border bg-muted/50 text-muted-foreground">
                <th className="py-3 px-4 font-semibold text-xs uppercase tracking-wider">Tenant Code</th>
                <th className="py-3 px-4 font-semibold text-xs uppercase tracking-wider">Tenant Name</th>
                <th className="py-3 px-4 font-semibold text-xs uppercase tracking-wider">Database</th>
                <th className="py-3 px-4 font-semibold text-xs uppercase tracking-wider">Admin Contact</th>
                <th className="py-3 px-4 font-semibold text-xs uppercase tracking-wider">Status</th>
                <th className="py-3 px-4 font-semibold text-xs uppercase tracking-wider text-right w-[250px]">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((tenant) => (
                <tr
                  key={tenant.id}
                  className={`border-b border-border text-foreground hover:bg-muted/30 transition-colors ${
                    !tenant.active ? 'opacity-60' : ''
                  }`}
                >
                  <td className="py-3.5 px-4 font-mono text-xs">
                    <span className="bg-muted px-2 py-0.5 rounded border border-border text-foreground">
                      {tenant.code}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-bold text-foreground">
                    {tenant.name}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-xs text-muted-foreground">{tenant.dbName}</td>
                  <td className="py-3.5 px-4 text-muted-foreground">{tenant.adminEmail || <span className="text-muted-foreground/60">—</span>}</td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold border ${
                        tenant.active
                          ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-600 dark:text-rose-455 border-rose-500/20'
                      }`}
                    >
                      {tenant.active ? 'Active' : 'Disabled'}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    {tenant.id === 1 ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[10px] uppercase font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                        System Master
                      </span>
                    ) : (
                      <div className="inline-flex items-center gap-3">
                        <button
                          type="button"
                          className="inline-flex items-center gap-1 font-semibold text-xs text-primary hover:text-primary/80 transition-colors"
                          onClick={() => {
                            setViewingTenantId(tenant.id);
                            setIsDetailsOpen(true);
                          }}
                        >
                          <Building className="w-3.5 h-3.5" />
                          Details
                        </button>
                        {hasPermission('TENANT_UPDATE') && (
                          <button
                            type="button"
                            className="inline-flex items-center gap-1 font-semibold text-xs text-amber-600 dark:text-amber-500 hover:opacity-85 transition-colors"
                            onClick={() => handleManageModules(tenant)}
                          >
                            <Sliders className="w-3.5 h-3.5" />
                            Modules
                          </button>
                        )}
                        {hasPermission('TENANT_UPDATE') && (
                          <button
                            type="button"
                            className={`inline-flex items-center gap-1 font-semibold text-xs transition-colors ${
                              tenant.active
                                ? 'text-rose-600 dark:text-rose-455 hover:opacity-85'
                                : 'text-emerald-600 dark:text-emerald-500 hover:opacity-85'
                            }`}
                            onClick={() => handleToggleStatus(tenant)}
                          >
                            {tenant.active ? (
                              <>
                                <ToggleLeft className="w-4 h-4" />
                                Disable
                              </>
                            ) : (
                              <>
                                <ToggleRight className="w-4 h-4" />
                                Enable
                              </>
                            )}
                          </button>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </EntityListPage>

      {/* Modern Overlay Modal for Module Subscription configuration */}
      {selectedTenant && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-border px-6 py-4 bg-muted/40">
              <div>
                <h3 className="text-base font-bold text-foreground flex items-center gap-2">
                  <Layers className="w-5 h-5 text-cyan-500" />
                  Grant Subscription Modules: <span className="text-cyan-500">{selectedTenant.name}</span>
                </h3>
                <p className="text-xs text-muted-foreground mt-1">
                  Adjust active system module clearance, license fees, and special billing arrangements.
                </p>
              </div>
              <button
                type="button"
                className="p-1 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                onClick={() => setSelectedTenant(null)}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Scroll Content */}
            <div className="p-6 space-y-4 max-h-[60vh] overflow-y-auto bg-muted/5">
              <div className="bg-cyan-500/10 border border-cyan-500/20 p-4 rounded-xl text-cyan-600 dark:text-cyan-400 text-xs flex gap-3">
                <ShieldAlert className="w-5 h-5 flex-shrink-0" />
                <div>
                  <span className="font-bold">Core Exemption:</span> SYSTEM_ADMIN and EMPLOYEE roles operate as system-core functions and do not require separate module enabling.
                </div>
              </div>

              <div className="space-y-4">
                {ALL_MODULES.map((moduleName) => {
                  const detail = moduleDetails[moduleName] || {
                    moduleName,
                    active: false,
                    amount: null,
                    paymentMethod: 'Card',
                    specialRequirements: '',
                    extraCharges: null,
                  };
                  return (
                    <div
                      key={moduleName}
                      className={`border rounded-xl p-4 transition-all duration-200 ${
                        detail.active
                          ? 'bg-cyan-500/5 border-cyan-500/30 shadow-md shadow-cyan-950/5'
                          : 'bg-background border-border hover:bg-muted/10'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex flex-col">
                          <span className="font-bold text-foreground text-sm">{moduleName} Module</span>
                          <span className="text-[10px] text-muted-foreground mt-0.5">
                            {moduleName === 'CRM' && 'Customer Relationship Management - Lead tracking and pipelines.'}
                            {moduleName === 'HRMS' && 'Human Resource Management System - Attendance, Shift & Payroll modules.'}
                            {moduleName === 'VENDOR' && 'Vendor Portal - Management dashboard and profiles.'}
                          </span>
                        </div>
                        <button
                          type="button"
                          className={`w-11 h-6 rounded-full p-0.5 transition-colors duration-200 focus:outline-none ${
                            detail.active ? 'bg-cyan-600' : 'bg-muted'
                          }`}
                          onClick={() => handleModuleDetailChange(moduleName, 'active', !detail.active)}
                        >
                          <div
                            className={`bg-card w-5 h-5 rounded-full shadow-md transform transition-transform duration-200 ${
                              detail.active ? 'translate-x-5' : 'translate-x-0'
                            }`}
                          />
                        </button>
                      </div>

                      {detail.active && (
                        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mt-4 pt-4 border-t border-border text-xs">
                          <div>
                            <label className="block text-muted-foreground mb-2 font-medium">Subscription Price</label>
                            <input
                              type="number"
                              className="w-full bg-background border border-border text-foreground rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
                              placeholder="e.g. 150"
                              value={detail.amount !== null ? detail.amount : ''}
                              onChange={(e) =>
                                handleModuleDetailChange(
                                  moduleName,
                                  'amount',
                                  e.target.value === '' ? null : Number(e.target.value)
                                )
                              }
                            />
                          </div>

                          <div>
                            <label className="block text-muted-foreground mb-2 font-medium">Payment Mode</label>
                            <select
                              className="w-full bg-background border border-border text-foreground rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
                              value={detail.paymentMethod}
                              onChange={(e) => handleModuleDetailChange(moduleName, 'paymentMethod', e.target.value)}
                            >
                              <option value="Card">Credit/Debit Card</option>
                              <option value="Cash">Cash</option>
                              <option value="Bank Transfer">Bank Transfer</option>
                              <option value="UPI / Wallet">UPI / Wallet</option>
                              <option value="Unpaid">Unpaid / Deferred</option>
                            </select>
                          </div>

                          <div>
                            <label className="block text-muted-foreground mb-2 font-medium">Special Requirements</label>
                            <input
                              type="text"
                              className="w-full bg-background border border-border text-foreground rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
                              placeholder="e.g. Specific branch code rules"
                              value={detail.specialRequirements || ''}
                              onChange={(e) => handleModuleDetailChange(moduleName, 'specialRequirements', e.target.value)}
                            />
                          </div>

                          <div>
                            <label className="block text-muted-foreground mb-2 font-medium">Extra Charges</label>
                            <input
                              type="number"
                              className="w-full bg-background border border-border text-foreground rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary"
                              placeholder="e.g. 50"
                              value={detail.extraCharges !== null ? detail.extraCharges : ''}
                              onChange={(e) =>
                                handleModuleDetailChange(
                                  moduleName,
                                  'extraCharges',
                                  e.target.value === '' ? null : Number(e.target.value)
                                )
                              }
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 border-t border-border px-6 py-4 bg-muted/40">
              <button
                type="button"
                className="px-4 py-2 bg-muted hover:bg-muted/80 border border-border rounded-xl text-foreground text-xs font-bold transition-colors"
                onClick={() => setSelectedTenant(null)}
                disabled={savingModules}
              >
                Cancel
              </button>
              <button
                type="button"
                className="px-5 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold flex items-center gap-2 transition-all active:scale-95 shadow-lg shadow-cyan-600/10"
                onClick={saveModules}
                disabled={savingModules}
              >
                {savingModules && <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />}
                {savingModules ? 'Saving Modules...' : 'Save Configuration'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Tenant Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Onboard New Tenant Workspace"
        size="3xl"
      >
        <CreateTenant
          onClose={() => setIsCreateOpen(false)}
          onSuccess={() => {
            setIsCreateOpen(false);
            fetchTenants();
          }}
        />
      </Modal>

      {/* Tenant Details Modal */}
      <Modal
        isOpen={isDetailsOpen}
        onClose={() => setIsDetailsOpen(false)}
        title="Tenant Workspace Details"
        size="3xl"
      >
        <TenantDetails
          tenantId={viewingTenantId}
          onClose={() => setIsDetailsOpen(false)}
        />
      </Modal>
    </div>
  );
}


