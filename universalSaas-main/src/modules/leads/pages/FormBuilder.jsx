// // src/modules/leads/pages/FormBuilder.jsx
// import React, { useEffect, useState } from 'react';
// import { Button } from '@/components/ui/button';
// import { Card } from '@/components/ui/card';
// import { Input } from '@/components/ui/input';
// import { useToast } from '@/context/ToastContext';
// import { Eye, Plus, Save, Trash2, Wrench } from 'lucide-react';
// import {
//   useGetLeadFormsQuery,
//   useSyncLeadFormFieldsMutation,
// } from '@/modules/leads/services/leadsApi';

// const fieldTypes = ['text', 'email', 'number', 'dropdown', 'checkbox', 'radio', 'date', 'textarea'];

// const normalizeField = (field, index) => ({
//   id: field.id,
//   label: field.label || '',
//   field_type: field.field_type || 'text',
//   required: Boolean(field.required),
//   placeholder: field.placeholder || '',
//   section: field.section || 'General Details',
//   validation: field.validation || {},
//   is_core: Boolean(field.is_core),
//   options: Array.isArray(field.options) ? field.options : [],
//   order: field.order ?? index + 1,
// });

// export default function FormBuilderPage() {
//   const toast = useToast();
//   const { data: forms = [], isLoading } = useGetLeadFormsQuery();
//   const [syncFields, { isLoading: saving }] = useSyncLeadFormFieldsMutation();
//   const form = forms.find((item) => item.is_active) || forms[0];
//   const [fields, setFields] = useState([]);

//   useEffect(() => {
//     if (form?.fields) {
//       setFields(form.fields.map(normalizeField));
//     }
//   }, [form?.id]);

//   const updateField = (index, key, value) => {
//     setFields((prev) => prev.map((field, fieldIndex) =>
//       fieldIndex === index ? { ...field, [key]: value } : field
//     ));
//   };

//   const addField = () => {
//     setFields((prev) => [
//       ...prev,
//       normalizeField({
//         label: 'New Field',
//         field_type: 'text',
//         section: 'General Details',
//         order: prev.length + 1,
//       }, prev.length),
//     ]);
//   };

//   const deleteField = (index) => {
//     setFields((prev) => prev.filter((field, fieldIndex) => field.is_core || fieldIndex !== index));
//   };

//   const save = async () => {
//     if (!form?.id) return;
//     try {
//       await syncFields({
//         formId: form.id,
//         fields: fields.map((field, index) => ({
//           ...field,
//           order: index + 1,
//           options: field.field_type === 'dropdown'
//             ? String(field.options || '').split(',').map((item) => item.trim()).filter(Boolean)
//             : field.options,
//         })),
//       }).unwrap();
//       toast.success('Saved', 'Lead intake form fields updated.');
//     } catch (err) {
//       toast.error('Error', err?.data?.detail || 'Failed to save form fields.');
//     }
//   };

//   if (isLoading) {
//     return <div className="p-6 text-muted-foreground">Loading form builder...</div>;
//   }

//   return (
//     <div className="space-y-8">
//       <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
//         <div>
//           <h1 className="text-3xl font-bold text-slate-950">Inquiry Form Builder</h1>
//           <p className="mt-2 text-slate-500">Customize layout, validations, and sections for student intake forms.</p>
//           <select className="mt-4 h-10 rounded-xl border border-slate-200 bg-white px-5 font-semibold text-violet-600">
//             <option>{form?.name || 'Active Intake Form'}</option>
//           </select>
//         </div>
//         <div className="flex gap-3">
//           <Button variant="outline" className="gap-2 rounded-xl bg-white">
//             <Wrench className="h-4 w-4" />
//             Designer
//           </Button>
//           <Button variant="outline" className="gap-2 rounded-xl bg-white">
//             <Eye className="h-4 w-4" />
//             Preview
//           </Button>
//           <Button className="h-12 gap-2 rounded-xl bg-violet-600 px-6 text-white hover:bg-violet-700" onClick={save} disabled={saving || !form}>
//             <Save className="h-4 w-4" />
//             Save Schema
//           </Button>
//         </div>
//       </div>

//       <div className="grid gap-8 xl:grid-cols-[360px_minmax(0,1fr)]">
//         <Card className="rounded-3xl bg-white p-6 shadow-sm">
//           <h2 className="mb-5 text-sm font-bold uppercase tracking-wide text-slate-600">Inputs Toolbox</h2>
//           <div className="space-y-3">
//             {fieldTypes.map((type) => (
//               <button
//                 type="button"
//                 key={type}
//                 onClick={addField}
//                 className="flex h-14 w-full items-center gap-4 rounded-2xl border border-slate-200 bg-slate-50/40 px-4 text-left font-semibold capitalize text-slate-600 hover:border-violet-200 hover:bg-violet-50"
//               >
//                 <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-slate-100 text-slate-500">
//                   <Plus className="h-4 w-4" />
//                 </span>
//                 {type === 'textarea' ? 'Multi-line Notes' : type.replace('-', ' ')}
//               </button>
//             ))}
//           </div>
//         </Card>

//         <Card className="rounded-3xl bg-white p-8 shadow-sm">
//           <div className="mb-6 flex items-center justify-between border-b border-slate-100 pb-5">
//             <h2 className="text-sm font-bold uppercase tracking-wide text-slate-600">Fields Canvas</h2>
//             <span className="text-xs font-bold uppercase text-slate-400">{fields.length} fields</span>
//           </div>
//           <div className="max-h-[620px] space-y-5 overflow-y-auto pr-2">
//             {fields.map((field, index) => (
//             <div key={field.id || index} className="rounded-3xl border border-slate-200 p-5">
//               <div className="mb-4 flex items-center justify-between">
//                 <span className="rounded-lg bg-violet-100 px-3 py-1 text-xs font-bold uppercase text-violet-600">
//                   {field.field_type}{field.is_core ? ' Core' : ''}
//                 </span>
//                 <Button
//                   variant="ghost"
//                   size="icon"
//                   disabled={field.is_core}
//                   onClick={() => deleteField(index)}
//                   className="text-slate-400 hover:text-rose-600"
//                 >
//                   <Trash2 className="h-4 w-4" />
//                 </Button>
//               </div>
//               <div className="grid gap-4 md:grid-cols-3">
//                 <label className="space-y-2 text-xs font-bold uppercase text-slate-400">
//                   Label
//                   <Input className="h-10 rounded-xl border-slate-200 bg-white text-sm normal-case text-slate-800" value={field.label} onChange={(event) => updateField(index, 'label', event.target.value)} />
//                 </label>
//                 <label className="space-y-2 text-xs font-bold uppercase text-slate-400">
//                   Placeholder
//                   <Input className="h-10 rounded-xl border-slate-200 bg-white text-sm normal-case text-slate-800" value={field.placeholder} onChange={(event) => updateField(index, 'placeholder', event.target.value)} />
//                 </label>
//                 <label className="space-y-2 text-xs font-bold uppercase text-slate-400">
//                   Section
//                   <Input className="h-10 rounded-xl border-slate-200 bg-white text-sm normal-case text-slate-800" value={field.section} onChange={(event) => updateField(index, 'section', event.target.value)} />
//                 </label>
//                 <label className="space-y-2 text-xs font-bold uppercase text-slate-400">
//                   Type
//                   <select
//                     value={field.field_type}
//                     onChange={(event) => updateField(index, 'field_type', event.target.value)}
//                     className="h-10 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm normal-case text-slate-800"
//                   >
//                     {fieldTypes.map((type) => <option key={type} value={type}>{type}</option>)}
//                   </select>
//                 </label>
//                 <label className="space-y-2 text-xs font-bold uppercase text-slate-400 md:col-span-2">
//                   Dropdown Options
//                   <Input
//                     className="h-10 rounded-xl border-slate-200 bg-white text-sm normal-case text-slate-800"
//                     value={Array.isArray(field.options) ? field.options.join(', ') : field.options || ''}
//                     onChange={(event) => updateField(index, 'options', event.target.value)}
//                     disabled={field.field_type !== 'dropdown'}
//                   />
//                 </label>
//               </div>
//               <label className="mt-4 flex items-center gap-2 text-sm font-semibold text-slate-600">
//                 <input
//                   type="checkbox"
//                   checked={field.required}
//                   onChange={(event) => updateField(index, 'required', event.target.checked)}
//                 />
//                 Required Field
//               </label>
//             </div>
//           ))}
//           </div>
//         </Card>
//         </div>
//     </div>
//   );
// }


// src/modules/leads/pages/FormBuilder.jsx
import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useToast } from '@/context/ToastContext';
import { Eye, Plus, Save, Trash2, Wrench } from 'lucide-react';
import {
  useGetLeadFormsQuery,
  useSyncLeadFormFieldsMutation,
} from '@/modules/leads/services/leadsApi';

const fieldTypes = ['text', 'email', 'number', 'dropdown', 'checkbox', 'radio', 'date', 'textarea'];

const normalizeField = (field, index) => ({
  id: field.id,
  label: field.label || '',
  field_type: field.field_type || 'text',
  required: Boolean(field.required),
  placeholder: field.placeholder || '',
  section: field.section || 'General Details',
  validation: field.validation || {},
  is_core: Boolean(field.is_core),
  options: Array.isArray(field.options) ? field.options : [],
  order: field.order ?? index + 1,
});

export default function FormBuilderPage() {
  const toast = useToast();
  const { data: forms = [], isLoading } = useGetLeadFormsQuery();
  const [syncFields, { isLoading: saving }] = useSyncLeadFormFieldsMutation();
  const form = forms.find((item) => item.is_active) || forms[0];
  const [fields, setFields] = useState([]);

  useEffect(() => {
    if (form?.fields) {
      setFields(form.fields.map(normalizeField));
    }
  }, [form?.id]);

  const updateField = (index, key, value) => {
    setFields((prev) => prev.map((field, fieldIndex) =>
      fieldIndex === index ? { ...field, [key]: value } : field
    ));
  };

  const addField = () => {
    setFields((prev) => [
      ...prev,
      normalizeField({
        label: 'New Field',
        field_type: 'text',
        section: 'General Details',
        order: prev.length + 1,
      }, prev.length),
    ]);
  };

  const deleteField = (index) => {
    setFields((prev) => prev.filter((field, fieldIndex) => field.is_core || fieldIndex !== index));
  };

  const save = async () => {
    if (!form?.id) return;
    try {
      await syncFields({
        formId: form.id,
        fields: fields.map((field, index) => ({
          ...field,
          order: index + 1,
          options: field.field_type === 'dropdown'
            ? String(field.options || '').split(',').map((item) => item.trim()).filter(Boolean)
            : field.options,
        })),
      }).unwrap();
      toast.success('Saved', 'Lead intake form fields updated.');
    } catch (err) {
      toast.error('Error', err?.data?.detail || 'Failed to save form fields.');
    }
  };

  if (isLoading) {
    return <div className="p-6 text-muted-foreground">Loading form builder...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Inquiry Form Builder</h1>
          <p className="mt-2 text-muted-foreground">Customize layout, validations, and sections for student intake forms.</p>
          <select className="mt-4 h-10 rounded-xl border border-border bg-background px-5 font-semibold text-violet-600">
            <option>{form?.name || 'Active Intake Form'}</option>
          </select>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" className="gap-2 rounded-xl bg-background text-foreground border-border">
            <Wrench className="h-4 w-4" />
            Designer
          </Button>
          <Button variant="outline" className="gap-2 rounded-xl bg-background text-foreground border-border">
            <Eye className="h-4 w-4" />
            Preview
          </Button>
          <Button className="h-12 gap-2 rounded-xl bg-violet-600 px-6 text-white hover:bg-violet-700" onClick={save} disabled={saving || !form}>
            <Save className="h-4 w-4" />
            Save Schema
          </Button>
        </div>
      </div>

      <div className="grid gap-8 xl:grid-cols-[360px_minmax(0,1fr)]">
        <Card className="rounded-3xl bg-card text-card-foreground p-6 shadow-sm border-border">
          <h2 className="mb-5 text-sm font-bold uppercase tracking-wide text-muted-foreground">Inputs Toolbox</h2>
          <div className="space-y-3">
            {fieldTypes.map((type) => (
              <button
                type="button"
                key={type}
                onClick={addField}
                className="flex h-14 w-full items-center gap-4 rounded-2xl border border-border bg-muted/20 px-4 text-left font-semibold capitalize text-foreground hover:border-violet-200 hover:bg-violet-50"
              >
                <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-muted text-muted-foreground">
                  <Plus className="h-4 w-4" />
                </span>
                {type === 'textarea' ? 'Multi-line Notes' : type.replace('-', ' ')}
              </button>
            ))}
          </div>
        </Card>

        <Card className="rounded-3xl bg-card text-card-foreground p-8 shadow-sm border-border">
          <div className="mb-6 flex items-center justify-between border-b border-border pb-5">
            <h2 className="text-sm font-bold uppercase tracking-wide text-muted-foreground">Fields Canvas</h2>
            <span className="text-xs font-bold uppercase text-muted-foreground">{fields.length} fields</span>
          </div>
          <div className="max-h-[620px] space-y-5 overflow-y-auto pr-2">
            {fields.map((field, index) => (
              <div key={field.id || index} className="rounded-3xl border border-border p-5">
                <div className="mb-4 flex items-center justify-between">
                  <span className="rounded-lg bg-violet-100 px-3 py-1 text-xs font-bold uppercase text-violet-600">
                    {field.field_type}{field.is_core ? ' Core' : ''}
                  </span>
                  <Button
                    variant="ghost"
                    size="icon"
                    disabled={field.is_core}
                    onClick={() => deleteField(index)}
                    className="text-muted-foreground hover:text-rose-600"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
                <div className="grid gap-4 md:grid-cols-3">
                  <label className="space-y-2 text-xs font-bold uppercase text-muted-foreground">
                    Label
                    <Input className="h-10 rounded-xl border-border bg-background text-sm normal-case text-foreground" value={field.label} onChange={(event) => updateField(index, 'label', event.target.value)} />
                  </label>
                  <label className="space-y-2 text-xs font-bold uppercase text-muted-foreground">
                    Placeholder
                    <Input className="h-10 rounded-xl border-border bg-background text-sm normal-case text-foreground" value={field.placeholder} onChange={(event) => updateField(index, 'placeholder', event.target.value)} />
                  </label>
                  <label className="space-y-2 text-xs font-bold uppercase text-muted-foreground">
                    Section
                    <Input className="h-10 rounded-xl border-border bg-background text-sm normal-case text-foreground" value={field.section} onChange={(event) => updateField(index, 'section', event.target.value)} />
                  </label>
                  <label className="space-y-2 text-xs font-bold uppercase text-muted-foreground">
                    Type
                    <select
                      value={field.field_type}
                      onChange={(event) => updateField(index, 'field_type', event.target.value)}
                      className="h-10 w-full rounded-xl border border-border bg-background px-3 text-sm normal-case text-foreground"
                    >
                      {fieldTypes.map((type) => <option key={type} value={type}>{type}</option>)}
                    </select>
                  </label>
                  <label className="space-y-2 text-xs font-bold uppercase text-muted-foreground md:col-span-2">
                    Dropdown Options
                    <Input
                      className="h-10 rounded-xl border-border bg-background text-sm normal-case text-foreground"
                      value={Array.isArray(field.options) ? field.options.join(', ') : field.options || ''}
                      onChange={(event) => updateField(index, 'options', event.target.value)}
                      disabled={field.field_type !== 'dropdown'}
                    />
                  </label>
                </div>
                <label className="mt-4 flex items-center gap-2 text-sm font-semibold text-foreground">
                  <input
                    type="checkbox"
                    checked={field.required}
                    onChange={(event) => updateField(index, 'required', event.target.checked)}
                  />
                  Required Field
                </label>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}