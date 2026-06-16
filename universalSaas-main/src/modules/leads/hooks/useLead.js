// src/modules/leads/hooks/useLead.js
import { useGetLeadQuery } from '@/modules/leads/services/leadsApi';
import { normalizeLead } from '@/modules/leads/hooks/useLeads';

export const useLead = (id) => {
  const query = useGetLeadQuery(id, { skip: !id });

  return {
    ...query,
    data: query.data ? normalizeLead(query.data) : undefined,
  };
};