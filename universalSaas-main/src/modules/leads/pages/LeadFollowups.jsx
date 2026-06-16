// import React, { useMemo, useState } from 'react';
// import { CheckCircle2, Loader2, Search } from 'lucide-react';
// import { Button } from '@/components/ui/button';
// import { Card } from '@/components/ui/card';
// import { Badge } from '@/components/ui/badge';
// import { useGetFollowUpsQuery, useGetLeadsQuery, useUpdateFollowUpMutation } from '@/modules/leads/services/leadsApi';
// import { formatDateTime, getLeadName, statusClass } from '@/modules/leads/utils/leadUi';
// import { useToast } from '@/context/ToastContext';

// const splitNote = (note = '') => {
//   const match = note.match(/^\[(.+?)\]\s*(.*)$/);
//   return {
//     method: match?.[1] || 'Call',
//     body: match?.[2] || note,
//   };
// };

// export default function LeadFollowups() {
//   const toast = useToast();
//   const [search, setSearch] = useState('');
//   const { data: leads = [], isLoading: leadsLoading } = useGetLeadsQuery();
//   const { data: followups = [], isLoading: followupsLoading } = useGetFollowUpsQuery();
//   const [updateFollowUp, { isLoading: updating }] = useUpdateFollowUpMutation();

//   const leadById = useMemo(() => {
//     const lookup = {};
//     leads.forEach((lead) => {
//       lookup[String(lead.id)] = lead;
//     });
//     return lookup;
//   }, [leads]);

//   const rows = useMemo(() => {
//     const query = search.trim().toLowerCase();
//     return followups
//       .map((followup) => ({ ...followup, lead: leadById[String(followup.lead_id)] }))
//       .filter((followup) => {
//         if (!query) return true;
//         const note = splitNote(followup.note);
//         return [getLeadName(followup.lead), followup.lead?.email, note.body, note.method]
//           .some((value) => String(value || '').toLowerCase().includes(query));
//       })
//       .sort((a, b) => {
//         if (a.completed !== b.completed) return a.completed ? 1 : -1;
//         return new Date(a.scheduled_at || a.created_at || 0) - new Date(b.scheduled_at || b.created_at || 0);
//       });
//   }, [followups, leadById, search]);

//   const complete = async (followup) => {
//     try {
//       await updateFollowUp({ id: followup.id, completed: true }).unwrap();
//       toast.success('Completed', 'Follow-up marked as completed.');
//     } catch (err) {
//       toast.error('Error', err?.data?.detail || 'Could not update follow-up.');
//     }
//   };

//   const loading = leadsLoading || followupsLoading;

//   return (
//     <div className="space-y-7">
//       <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
//         <div>
//           <h1 className="text-3xl font-bold text-slate-950">Follow Ups</h1>
//           <p className="mt-2 text-slate-500">Tracks scheduled lead conversations and pending counselor actions.</p>
//         </div>
//         <label className="relative w-full md:w-96">
//           <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
//           <input
//             value={search}
//             onChange={(event) => setSearch(event.target.value)}
//             placeholder="Search follow ups..."
//             className="h-12 w-full rounded-xl border border-slate-200 bg-white pl-12 pr-4 outline-none focus:border-violet-300 focus:ring-4 focus:ring-violet-100"
//           />
//         </label>
//       </div>

//       {loading ? (
//         <div className="flex items-center justify-center gap-3 py-20 text-slate-500">
//           <Loader2 className="h-5 w-5 animate-spin" />
//           Loading follow ups...
//         </div>
//       ) : rows.length === 0 ? (
//         <Card className="rounded-3xl bg-white p-16 text-center text-slate-400">No follow ups found.</Card>
//       ) : (
//         <div className="space-y-5">
//           {rows.map((followup) => {
//             const note = splitNote(followup.note);
//             const lead = followup.lead;
//             return (
//               <Card key={followup.id} className="rounded-3xl bg-white p-7 shadow-sm">
//                 <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
//                   <div>
//                     <div className="flex flex-wrap items-center gap-3">
//                       <h2 className="text-xl font-bold text-slate-900">{getLeadName(lead)}</h2>
//                       <Badge variant="outline" className={`gap-1.5 rounded-full px-3 py-1 text-xs font-bold ${statusClass(lead?.status)}`}>
//                         <span className="h-1.5 w-1.5 rounded-full bg-current" />
//                         {lead?.status || 'New'}
//                       </Badge>
//                     </div>
//                     <p className="mt-2 text-slate-500">{lead?.email || 'No email'}</p>
//                     <p className="mt-5 text-lg font-semibold text-slate-700">[{note.method}] {note.body}</p>
//                   </div>
//                   <div className="flex shrink-0 flex-col items-start gap-3 lg:items-end">
//                     <span className={`rounded-full px-4 py-1.5 text-xs font-bold uppercase ${followup.completed ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>
//                       {followup.completed ? 'Completed' : 'Pending'}
//                     </span>
//                     <span className="text-lg font-bold text-slate-400">{formatDateTime(followup.scheduled_at || followup.created_at)}</span>
//                     {!followup.completed && (
//                       <Button disabled={updating} onClick={() => complete(followup)} className="gap-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-700">
//                         <CheckCircle2 className="h-4 w-4" />
//                         Complete
//                       </Button>
//                     )}
//                   </div>
//                 </div>
//               </Card>
//             );
//           })}
//         </div>
//       )}
//     </div>
//   );
// }


import React, { useMemo, useState } from 'react';
import { CheckCircle2, Loader2, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useGetFollowUpsQuery, useGetLeadsQuery, useUpdateFollowUpMutation } from '@/modules/leads/services/leadsApi';
import { formatDateTime, getLeadName, statusClass } from '@/modules/leads/utils/leadUi';
import { useToast } from '@/context/ToastContext';

const splitNote = (note = '') => {
  const match = note.match(/^\[(.+?)\]\s*(.*)$/);
  return {
    method: match?.[1] || 'Call',
    body: match?.[2] || note,
  };
};

export default function LeadFollowups() {
  const toast = useToast();
  const [search, setSearch] = useState('');
  const { data: leads = [], isLoading: leadsLoading } = useGetLeadsQuery();
  const { data: followups = [], isLoading: followupsLoading } = useGetFollowUpsQuery();
  const [updateFollowUp, { isLoading: updating }] = useUpdateFollowUpMutation();

  const leadById = useMemo(() => {
    const lookup = {};
    leads.forEach((lead) => {
      lookup[String(lead.id)] = lead;
    });
    return lookup;
  }, [leads]);

  const rows = useMemo(() => {
    const query = search.trim().toLowerCase();
    return followups
      .map((followup) => ({ ...followup, lead: leadById[String(followup.lead_id)] }))
      .filter((followup) => {
        if (!query) return true;
        const note = splitNote(followup.note);
        return [getLeadName(followup.lead), followup.lead?.email, note.body, note.method]
          .some((value) => String(value || '').toLowerCase().includes(query));
      })
      .sort((a, b) => {
        if (a.completed !== b.completed) return a.completed ? 1 : -1;
        return new Date(a.scheduled_at || a.created_at || 0) - new Date(b.scheduled_at || b.created_at || 0);
      });
  }, [followups, leadById, search]);

  const complete = async (followup) => {
    try {
      await updateFollowUp({ id: followup.id, completed: true }).unwrap();
      toast.success('Completed', 'Follow-up marked as completed.');
    } catch (err) {
      toast.error('Error', err?.data?.detail || 'Could not update follow-up.');
    }
  };

  const loading = leadsLoading || followupsLoading;

  return (
    <div className="space-y-7">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Follow Ups</h1>
          <p className="mt-2 text-muted-foreground">Tracks scheduled lead conversations and pending counselor actions.</p>
        </div>
        <label className="relative w-full md:w-96">
          <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search follow ups..."
            className="h-12 w-full rounded-xl border border-border bg-background text-foreground pl-12 pr-4 outline-none focus:border-violet-300 focus:ring-4 focus:ring-violet-100/30"
          />
        </label>
      </div>

      {loading ? (
        <div className="flex items-center justify-center gap-3 py-20 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          Loading follow ups...
        </div>
      ) : rows.length === 0 ? (
        <Card className="rounded-3xl bg-card text-card-foreground p-16 text-center text-muted-foreground border-border">No follow ups found.</Card>
      ) : (
        <div className="space-y-5">
          {rows.map((followup) => {
            const note = splitNote(followup.note);
            const lead = followup.lead;
            return (
              <Card key={followup.id} className="rounded-3xl bg-card text-card-foreground p-7 shadow-sm border-border">
                <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <h2 className="text-xl font-bold text-foreground">{getLeadName(lead)}</h2>
                      <Badge variant="outline" className={`gap-1.5 rounded-full px-3 py-1 text-xs font-bold border ${statusClass(lead?.status)}`}>
                        <span className="h-1.5 w-1.5 rounded-full bg-current" />
                        {lead?.status || 'New'}
                      </Badge>
                    </div>
                    <p className="mt-2 text-muted-foreground">{lead?.email || 'No email'}</p>
                    <p className="mt-5 text-lg font-semibold text-foreground/90">[{note.method}] {note.body}</p>
                  </div>
                  <div className="flex shrink-0 flex-col items-start gap-3 lg:items-end">
                    <span className={`rounded-full px-4 py-1.5 text-xs font-bold uppercase ${followup.completed ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>
                      {followup.completed ? 'Completed' : 'Pending'}
                    </span>
                    <span className="text-lg font-bold text-muted-foreground">{formatDateTime(followup.scheduled_at || followup.created_at)}</span>
                    {!followup.completed && (
                      <Button disabled={updating} onClick={() => complete(followup)} className="gap-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-700">
                        <CheckCircle2 className="h-4 w-4" />
                        Complete
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}