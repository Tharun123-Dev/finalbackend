// // src/modules/leads/pages/LeadOptions.jsx
// import React, { useEffect, useState } from 'react';
// import { Button } from '@/components/ui/button';
// import { Card } from '@/components/ui/card';
// import { Input } from '@/components/ui/input';
// import { ArrowDown, ArrowUp, Plus, Save, Trash2 } from 'lucide-react';
// import { useToast } from '@/context/ToastContext';
// import { useGetLeadOptionsQuery, useSaveLeadOptionsMutation } from '@/modules/leads/services/leadsApi';

// const normalize = (items = []) => items.map((item, index) => ({
//   id: item.id,
//   label: item.label || item.value || '',
//   value: item.value || item.label || '',
//   sort_order: item.sort_order || index + 1,
//   color: item.color || '',
// }));

// function OptionEditor({ title, items, onChange, onAdd, onRemove, onMove }) {
//   return (
//     <Card className="rounded-3xl bg-white p-7 shadow-sm">
//       <div className="mb-5 flex items-center justify-between">
//         <div>
//           <h2 className="text-xl font-bold text-slate-950">{title}</h2>
//           <p className="mt-1 text-slate-400">{items.length} active options</p>
//         </div>
//         <Button variant="outline" className="gap-2 rounded-xl bg-indigo-50 text-indigo-600" onClick={onAdd}>
//           <Plus className="h-4 w-4" />
//           Add
//         </Button>
//       </div>
//       <div className="space-y-4">
//         {items.map((item, index) => (
//           <div key={item.id || index} className="grid gap-3 rounded-2xl border border-slate-200 bg-slate-50/30 p-4 md:grid-cols-[1fr_1fr_auto]">
//             <Input
//               value={item.label}
//               onChange={(event) => onChange(index, 'label', event.target.value)}
//               placeholder="Label"
//               className="h-12 rounded-xl border-slate-200 bg-white px-4 font-semibold"
//             />
//             <Input
//               value={item.value}
//               onChange={(event) => onChange(index, 'value', event.target.value)}
//               placeholder="Value"
//               className="h-12 rounded-xl border-slate-200 bg-white px-4"
//             />
//             <div className="flex items-center justify-end gap-1">
//               <Button variant="ghost" size="icon" className="text-slate-400" onClick={() => onMove(index, -1)} disabled={index === 0}>
//                 <ArrowUp className="h-4 w-4" />
//               </Button>
//               <Button variant="ghost" size="icon" className="text-slate-400" onClick={() => onMove(index, 1)} disabled={index === items.length - 1}>
//                 <ArrowDown className="h-4 w-4" />
//               </Button>
//               <Button variant="ghost" size="icon" className="text-slate-400 hover:text-rose-600" onClick={() => onRemove(index)}>
//                 <Trash2 className="h-4 w-4" />
//               </Button>
//             </div>
//           </div>
//         ))}
//       </div>
//     </Card>
//   );
// }

// export default function LeadOptions() {
//   const toast = useToast();
//   const { data, isLoading } = useGetLeadOptionsQuery();
//   const [saveOptions, { isLoading: saving }] = useSaveLeadOptionsMutation();
//   const [statuses, setStatuses] = useState([]);
//   const [contactMethods, setContactMethods] = useState([]);

//   useEffect(() => {
//     if (data) {
//       setStatuses(normalize(data.statuses));
//       setContactMethods(normalize(data.contact_methods));
//     }
//   }, [data]);

//   const change = (setter) => (index, key, value) => {
//     setter((prev) => prev.map((item, itemIndex) =>
//       itemIndex === index ? { ...item, [key]: value } : item
//     ));
//   };

//   const add = (setter) => {
//     setter((prev) => [...prev, { label: 'New Option', value: 'New Option', sort_order: prev.length + 1 }]);
//   };

//   const remove = (setter) => (index) => {
//     setter((prev) => prev.filter((_, itemIndex) => itemIndex !== index));
//   };

//   const move = (setter) => (index, direction) => {
//     setter((prev) => {
//       const nextIndex = index + direction;
//       if (nextIndex < 0 || nextIndex >= prev.length) return prev;
//       const copy = [...prev];
//       [copy[index], copy[nextIndex]] = [copy[nextIndex], copy[index]];
//       return copy;
//     });
//   };

//   const handleSave = async () => {
//     try {
//       await saveOptions({
//         statuses: statuses.map((item, index) => ({ ...item, sort_order: index + 1 })),
//         contact_methods: contactMethods.map((item, index) => ({ ...item, sort_order: index + 1 })),
//       }).unwrap();
//       toast.success('Saved', 'Lead dropdown settings updated.');
//     } catch (err) {
//       toast.error('Error', err?.data?.detail || 'Failed to save lead options.');
//     }
//   };

//   if (isLoading) return <div className="p-6 text-muted-foreground">Loading lead dropdown settings...</div>;

//   return (
//     <div className="space-y-8">
//       <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
//         <div>
//           <h1 className="text-3xl font-bold text-slate-950">Lead Dropdown Settings</h1>
//           <p className="mt-2 text-slate-500">Manage the statuses and contact methods used in lead forms, filters, and follow-up logging.</p>
//         </div>
//         <Button className="h-14 gap-2 rounded-xl bg-violet-600 px-7 text-white hover:bg-violet-700" onClick={handleSave} disabled={saving}>
//           <Save className="h-4 w-4" />
//           Save Changes
//         </Button>
//       </div>
//       <div className="grid gap-6 xl:grid-cols-2">
//         <OptionEditor
//           title="Lead Statuses"
//           items={statuses}
//           onChange={change(setStatuses)}
//           onAdd={() => add(setStatuses)}
//           onRemove={remove(setStatuses)}
//           onMove={move(setStatuses)}
//         />
//         <OptionEditor
//           title="Contact Methods"
//           items={contactMethods}
//           onChange={change(setContactMethods)}
//           onAdd={() => add(setContactMethods)}
//           onRemove={remove(setContactMethods)}
//           onMove={move(setContactMethods)}
//         />
//       </div>
//     </div>
//   );
// }


// src/modules/leads/pages/LeadOptions.jsx
import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ArrowDown, ArrowUp, Plus, Save, Trash2 } from 'lucide-react';
import { useToast } from '@/context/ToastContext';
import { useGetLeadOptionsQuery, useSaveLeadOptionsMutation } from '@/modules/leads/services/leadsApi';

const normalize = (items = []) => items.map((item, index) => ({
  id: item.id,
  label: item.label || item.value || '',
  value: item.value || item.label || '',
  sort_order: item.sort_order || index + 1,
  color: item.color || '',
}));

function OptionEditor({ title, items, onChange, onAdd, onRemove, onMove }) {
  return (
    <Card className="rounded-3xl bg-card text-card-foreground p-7 shadow-sm border-border">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground">{title}</h2>
          <p className="mt-1 text-muted-foreground">{items.length} active options</p>
        </div>
        <Button variant="outline" className="gap-2 rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/40 dark:text-indigo-400" onClick={onAdd}>
          <Plus className="h-4 w-4" />
          Add
        </Button>
      </div>
      <div className="space-y-4">
        {items.map((item, index) => (
          <div key={item.id || index} className="grid gap-3 rounded-2xl border border-border bg-muted/20 p-4 md:grid-cols-[1fr_1fr_auto]">
            <Input
              value={item.label}
              onChange={(event) => onChange(index, 'label', event.target.value)}
              placeholder="Label"
              className="h-12 rounded-xl border-border bg-background text-foreground px-4 font-semibold"
            />
            <Input
              value={item.value}
              onChange={(event) => onChange(index, 'value', event.target.value)}
              placeholder="Value"
              className="h-12 rounded-xl border-border bg-background text-foreground px-4"
            />
            <div className="flex items-center justify-end gap-1">
              <Button variant="ghost" size="icon" className="text-muted-foreground" onClick={() => onMove(index, -1)} disabled={index === 0}>
                <ArrowUp className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="text-muted-foreground" onClick={() => onMove(index, 1)} disabled={index === items.length - 1}>
                <ArrowDown className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-rose-600" onClick={() => onRemove(index)}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

export default function LeadOptions() {
  const toast = useToast();
  const { data, isLoading } = useGetLeadOptionsQuery();
  const [saveOptions, { isLoading: saving }] = useSaveLeadOptionsMutation();
  const [statuses, setStatuses] = useState([]);
  const [contactMethods, setContactMethods] = useState([]);

  useEffect(() => {
    if (data) {
      setStatuses(normalize(data.statuses));
      setContactMethods(normalize(data.contact_methods));
    }
  }, [data]);

  const change = (setter) => (index, key, value) => {
    setter((prev) => prev.map((item, itemIndex) =>
      itemIndex === index ? { ...item, [key]: value } : item
    ));
  };

  const add = (setter) => {
    setter((prev) => [...prev, { label: 'New Option', value: 'New Option', sort_order: prev.length + 1 }]);
  };

  const remove = (setter) => (index) => {
    setter((prev) => prev.filter((_, itemIndex) => itemIndex !== index));
  };

  const move = (setter) => (index, direction) => {
    setter((prev) => {
      const nextIndex = index + direction;
      if (nextIndex < 0 || nextIndex >= prev.length) return prev;
      const copy = [...prev];
      [copy[index], copy[nextIndex]] = [copy[nextIndex], copy[index]];
      return copy;
    });
  };

  const handleSave = async () => {
    try {
      await saveOptions({
        statuses: statuses.map((item, index) => ({ ...item, sort_order: index + 1 })),
        contact_methods: contactMethods.map((item, index) => ({ ...item, sort_order: index + 1 })),
      }).unwrap();
      toast.success('Saved', 'Lead dropdown settings updated.');
    } catch (err) {
      toast.error('Error', err?.data?.detail || 'Failed to save lead options.');
    }
  };

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading lead dropdown settings...</div>;

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Lead Dropdown Settings</h1>
          <p className="mt-2 text-muted-foreground">Manage the statuses and contact methods used in lead forms, filters, and follow-up logging.</p>
        </div>
        <Button className="h-14 gap-2 rounded-xl bg-violet-600 px-7 text-white hover:bg-violet-700" onClick={handleSave} disabled={saving}>
          <Save className="h-4 w-4" />
          Save Changes
        </Button>
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <OptionEditor
          title="Lead Statuses"
          items={statuses}
          onChange={change(setStatuses)}
          onAdd={() => add(setStatuses)}
          onRemove={remove(setStatuses)}
          onMove={move(setStatuses)}
        />
        <OptionEditor
          title="Contact Methods"
          items={contactMethods}
          onChange={change(setContactMethods)}
          onAdd={() => add(setContactMethods)}
          onRemove={remove(setContactMethods)}
          onMove={move(setContactMethods)}
        />
      </div>
    </div>
  );
}