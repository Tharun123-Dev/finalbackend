import api from '@/services/api';
import type { DashboardStatsResponse, ActivityLog } from '@/types/dashboard-api';

export function getDashboardStats() {
  // Expected to return DashboardStatsResponse
  return api.get<DashboardStatsResponse>('/dashboard/stats').then(res => res.data);
}

export function getActivityLog() {
  // Expeected to return ActivityLog[]
  return api.get<ActivityLog[]>('/dashboard/activity').then(res => res.data);
}


