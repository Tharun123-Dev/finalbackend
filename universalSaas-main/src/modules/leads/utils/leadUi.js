export const optionValue = (item) =>
  typeof item === 'string' ? item : item?.value || item?.label || '';

export const optionLabel = (item) =>
  typeof item === 'string' ? item : item?.label || item?.value || '';

export const toOptions = (items = []) =>
  items.map((item) => ({
    label: optionLabel(item),
    value: optionValue(item),
  }));

export const getFieldValue = (lead, labels) => {
  const accepted = labels.map((label) => label.toLowerCase());
  return lead?.field_values?.find((item) =>
    accepted.includes(String(item.field?.label || '').trim().toLowerCase())
  )?.value || '';
};

export const getLeadName = (lead) => lead?.full_name || lead?.name || 'Unknown Lead';

export const getLeadCourse = (lead) =>
  lead?.course || getFieldValue(lead, ['Course of Interest', 'Course', 'Program']) || 'N/A';

export const getLeadSource = (lead) =>
  lead?.source || getFieldValue(lead, ['Source', 'Lead Source']) || 'N/A';

export const getLeadNotes = (lead) =>
  lead?.internal_notes || getFieldValue(lead, ['Internal Notes', 'Notes']) || '';

export const getLeadCounselor = (lead) =>
  lead?.counselor?.full_name ||
  lead?.counselor?.email ||
  lead?.assigned_to?.name ||
  'Unassigned';

export const formatShortDate = (date) =>
  date
    ? new Date(date).toLocaleDateString('en-US', {
        month: 'numeric',
        day: 'numeric',
        year: 'numeric',
      })
    : 'N/A';

export const formatDateTime = (date) =>
  date
    ? new Date(date).toLocaleString('en-US', {
        month: 'numeric',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      })
    : '';

export const statusClass = (status) => {
  const classes = {
    New: 'bg-cyan-50 text-cyan-700 border-cyan-200',
    Contacted: 'bg-slate-50 text-slate-700 border-slate-200',
    Interested: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    'Follow-Up Pending': 'bg-amber-50 text-amber-700 border-amber-200',
    'Admission Confirmed': 'bg-indigo-50 text-indigo-700 border-indigo-200',
    Rejected: 'bg-rose-50 text-rose-700 border-rose-200',
  };
  return classes[status] || 'bg-slate-50 text-slate-700 border-slate-200';
};
