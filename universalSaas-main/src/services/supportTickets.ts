import rolesApi from './rolesApi';

export interface TicketType {
  id: number;
  name: string;
  code: string;
  description?: string;
  is_active?: boolean;
}

export interface TicketNote {
  id: string;
  author_name: string;
  note: string;
  created_at: string;
  status_from?: string;
  status_to?: string;
  is_internal?: boolean;
}

export interface Ticket {
  id: number;
  ticket_no: string;
  subject: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'open' | 'in_progress' | 'waiting_user' | 'resolved' | 'closed' | 'reopened';
  issue_type_name: string;
  issue_type: string;
  description: string;
  requester_name: string;
  assigned_to_name?: string;
  resolved_by_name?: string;
  created_at: string;
  updated_at?: string;
  notes?: TicketNote[];
}

export interface TicketSummary {
  total: number;
  open: number;
  in_progress: number;
  waiting_user: number;
  resolved: number;
  closed: number;
  scope: 'all' | 'mine';
}

export const supportTicketsService = {
  getTypes: () => rolesApi.get<TicketType[]>('/support/ticket-types/'),
  createType: (data: { name: string; code: string; description?: string }) => 
    rolesApi.post<TicketType>('/support/ticket-types/', data),
  deleteType: (id: number) => rolesApi.delete(`/support/ticket-types/${id}/`),
  raise: (data: { issue_type: string; priority: string; subject: string; description: string }) => 
    rolesApi.post<Ticket>('/support/tickets/raise/', data),
  myTickets: () => rolesApi.get<Ticket[]>('/support/tickets/my/'),
  allTickets: (params?: Record<string, string>) => 
    rolesApi.get<Ticket[]>('/support/tickets/all/', { params }),
  summary: () => rolesApi.get<TicketSummary>('/support/tickets/summary/'),
  action: (id: number, data: { action: string; note: string; is_internal?: boolean }) => 
    rolesApi.post<Ticket>(`/support/tickets/${id}/action/`, data),
};

