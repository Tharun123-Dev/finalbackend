import React, { useState } from 'react';
import { Search, Filter, ArrowUpRight, CheckCircle2, AlertCircle, XCircle, DollarSign, Wallet, X } from 'lucide-react';
import { useAffiliate } from '../context/AffiliateContext';
import { Referral } from '../types';

export const Referrals: React.FC = () => {
  const { referrals, loading } = useAffiliate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'converted' | 'cancelled'>('all');
  const [selectedReferral, setSelectedReferral] = useState<Referral | null>(null);

  const getStatusBadge = (status: Referral['status']) => {
    switch (status) {
      case 'converted':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400">
            <CheckCircle2 size={12} />
            Converted
          </span>
        );
      case 'pending':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400">
            <AlertCircle size={12} />
            Pending
          </span>
        );
      case 'cancelled':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-400">
            <XCircle size={12} />
            Cancelled
          </span>
        );
    }
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val);
  };

  const filteredReferrals = referrals.filter((ref) => {
    const matchesSearch = ref.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          ref.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          ref.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || ref.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-primary-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-foreground">Referral Management</h2>
        <p className="text-xs text-muted-foreground">
          Manage, track, and filter your referred customers and their conversion status.
        </p>
      </div>

      {/* Filter and Search controls */}
      <div className="flex flex-col sm:flex-row items-center gap-4 bg-card p-4 rounded-2xl border border-border shadow-sm">
        <div className="relative w-full sm:flex-grow">
          <input
            type="text"
            placeholder="Search by ID, name or email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl border bg-slate-50 dark:bg-slate-900 border-border text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
          />
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
        </div>

        <div className="flex items-center gap-2.5 w-full sm:w-auto">
          <Filter size={16} className="text-slate-400 hidden sm:block" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as 'all' | 'pending' | 'converted' | 'cancelled')}
            className="w-full sm:w-36 px-3 py-2 rounded-xl border bg-slate-50 dark:bg-slate-900 border-border text-sm font-semibold text-slate-700 dark:text-slate-300 focus:outline-none"
          >
            <option value="all">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="converted">Converted</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Referrals Table Panel */}
      <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs md:text-sm">
            <thead>
              <tr className="border-b border-border text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                <th className="pb-3.5 pl-2">Referral ID</th>
                <th className="pb-3.5">Customer Details</th>
                <th className="pb-3.5">Referral Date</th>
                <th className="pb-3.5">Status</th>
                <th className="pb-3.5 text-right">Purchase Amount</th>
                <th className="pb-3.5 pr-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100/50 dark:divide-slate-900/50">
              {filteredReferrals.map((ref) => (
                <tr 
                  key={ref.id} 
                  className="hover:bg-slate-50/50 dark:hover:bg-slate-900/40 transition-colors cursor-pointer" 
                  onClick={() => setSelectedReferral(ref)}
                >
                  <td className="py-4 pl-2 font-mono text-xs font-bold text-muted-foreground">
                    {ref.id}
                  </td>
                  <td className="py-4">
                    <div className="flex items-center gap-3">
                      <img src={ref.avatar} className="w-10 h-10 rounded-full object-cover border border-border shadow-sm" alt={ref.name} />
                      <div>
                        <p className="font-bold text-slate-900 dark:text-white">{ref.name}</p>
                        <p className="text-[11px] text-muted-foreground font-semibold">{ref.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 font-semibold text-muted-foreground">
                    {new Date(ref.joinedDate).toLocaleDateString()}
                  </td>
                  <td className="py-4">
                    {getStatusBadge(ref.status)}
                  </td>
                  <td className="py-4 text-right font-black text-slate-900 dark:text-white">
                    {formatCurrency(ref.totalSpent)}
                  </td>
                  <td className="py-4 text-right pr-2">
                    <button className="p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-900 transition text-muted-foreground hover:text-indigo-600">
                      <ArrowUpRight size={16} />
                    </button>
                  </td>
                </tr>
              ))}
              {filteredReferrals.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-muted-foreground">
                    No matching referral records found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail Modal Overlay */}
      {selectedReferral && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs">
          <div className="bg-card border border-border rounded-3xl w-full max-w-2xl overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-border p-5">
              <h3 className="font-extrabold text-base text-slate-900 dark:text-white">Referral Account Details</h3>
              <button 
                onClick={() => setSelectedReferral(null)}
                className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-6 space-y-6">
              <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4">
                <img 
                  src={selectedReferral.avatar} 
                  alt={selectedReferral.name} 
                  className="w-20 h-20 rounded-full border-4 border-indigo-500/10 object-cover shadow-md" 
                />
                <div className="text-center sm:text-left space-y-1">
                  <h4 className="text-lg font-bold text-slate-900 dark:text-white">{selectedReferral.name}</h4>
                  <p className="text-xs text-muted-foreground font-semibold">{selectedReferral.email}</p>
                  <div className="mt-2 flex items-center justify-center sm:justify-start gap-2">
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-400">
                      {selectedReferral.plan}
                    </span>
                    {getStatusBadge(selectedReferral.status)}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-slate-50 dark:bg-background p-4 rounded-2xl border border-border flex items-center justify-between">
                  <div>
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Total Client Spending</span>
                    <h5 className="text-lg font-black text-foreground mt-1">{formatCurrency(selectedReferral.totalSpent)}</h5>
                  </div>
                  <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-600">
                    <Wallet size={18} />
                  </div>
                </div>

                <div className="bg-slate-50 dark:bg-background p-4 rounded-2xl border border-border flex items-center justify-between">
                  <div>
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Commissions Earned</span>
                    <h5 className="text-lg font-black text-foreground mt-1">{formatCurrency(selectedReferral.commission)}</h5>
                  </div>
                  <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-600">
                    <DollarSign size={18} />
                  </div>
                </div>
              </div>

              {/* Campaign details logs */}
              <div className="bg-slate-50 dark:bg-background p-5 rounded-2xl border border-border space-y-4">
                <div className="flex justify-between border-b border-border pb-2.5 text-xs text-slate-500">
                  <span>Commission Rule Tier</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{selectedReferral.tier}</span>
                </div>
                
                <div className="space-y-3">
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Technical UTM logs</p>
                  <div className="p-3 bg-card rounded-xl border border-slate-200/50 dark:border-slate-800 font-mono text-[10px] text-muted-foreground space-y-1">
                    <div>[UTM_SOURCE] : youtube-review-sarah</div>
                    <div>[UTM_CAMPAIGN] : spring-promotion-2026</div>
                    <div>[REFERRER_DOMAIN] : youtube.com</div>
                    <div>[API_STATUS] : success (ping-back complete)</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-slate-50 dark:bg-background border-t border-border p-4 flex justify-end gap-2">
              <button 
                onClick={() => setSelectedReferral(null)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition shadow-md shadow-indigo-500/20 cursor-pointer"
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Referrals;


