import type { DashboardStatsResponse, ActivityLog } from '@/types/dashboard-api';

/**
 * Dashboard hook that returns empty data when the backend is unavailable.
 * This avoids rendering errors caused by incomplete mock StatWidget objects.
 */
export function useDashboard() {
  const stats: DashboardStatsResponse = [];
  const activities: ActivityLog = [];
  const loading = false;

  return { stats, activities, loading };
}


