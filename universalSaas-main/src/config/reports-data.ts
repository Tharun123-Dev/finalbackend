import type {
  BreakdownPoint,
  GeneratedReport,
  MonthlyTrendPoint,
  ReportDisplayConfig,
  ReportSummary,
} from '@/types/reports'

export const DEFAULT_REPORT_DISPLAY_CONFIG: ReportDisplayConfig = {
  usersTrend: { enabled: true, chartType: 'bar' },
  revenueTrend: { enabled: true, chartType: 'line' },
  usersByRole: { enabled: true, chartType: 'pie' },
  revenueBySource: { enabled: true, chartType: 'pie' },
  usersVsRevenue: { enabled: true, chartType: 'area' },
}

export const REPORT_DISPLAY_STORAGE_KEY = 'universal-report-display-config'

export const monthlyTrendData: MonthlyTrendPoint[] = [
  { month: '2026-01', label: 'Jan', users: 2100, newUsers: 180, revenue: 3200000, growth: 12 },
  { month: '2026-02', label: 'Feb', users: 2280, newUsers: 195, revenue: 3800000, growth: 18 },
  { month: '2026-03', label: 'Mar', users: 2410, newUsers: 210, revenue: 3500000, growth: 8 },
  { month: '2026-04', label: 'Apr', users: 2580, newUsers: 225, revenue: 4200000, growth: 20 },
  { month: '2026-05', label: 'May', users: 2720, newUsers: 240, revenue: 4100000, growth: 15 },
  { month: '2026-06', label: 'Jun', users: 2847, newUsers: 127, revenue: 4820000, growth: 22 },
]

export const usersByRole: BreakdownPoint[] = [
  { name: 'Admin', value: 42, color: '#6366f1' },
  { name: 'Manager', value: 186, color: '#8b5cf6' },
  { name: 'Employee', value: 2340, color: '#10b981' },
  { name: 'Viewer', value: 279, color: '#f59e0b' },
]

export const revenueBySource: BreakdownPoint[] = [
  { name: 'Subscriptions', value: 2850000, color: '#6366f1' },
  { name: 'Services', value: 1120000, color: '#10b981' },
  { name: 'Add-ons', value: 580000, color: '#f59e0b' },
  { name: 'Other', value: 270000, color: '#94a3b8' },
]

export const generatedReportsSeed: GeneratedReport[] = [
  { id: 'RPT-001', name: 'Users & Revenue Summary Q2', type: 'Analytics', metrics: ['users', 'revenue'], date: '2026-05-20', status: 'Ready', branchId: 'branch_hq' },
  { id: 'RPT-002', name: 'Monthly User Growth', type: 'Users', metrics: ['users'], date: '2026-05-19', status: 'Ready', branchId: 'branch_hq' },
  { id: 'RPT-003', name: 'Revenue by Source — May', type: 'Revenue', metrics: ['revenue'], date: '2026-05-18', status: 'Processing', branchId: 'branch_del' },
  { id: 'RPT-004', name: 'Combined Users & Revenue', type: 'Analytics', metrics: ['users', 'revenue'], date: '2026-05-17', status: 'Ready', branchId: 'branch_hq' },
  { id: 'RPT-005', name: 'Branch Comparison Report', type: 'Analytics', metrics: ['users', 'revenue'], date: '2026-05-15', status: 'Ready', branchId: 'all' },
]

export function computeReportSummary(
  trend: MonthlyTrendPoint[],
  dateFrom: string,
  dateTo: string
): ReportSummary {
  const filtered = trend.filter((p) => p.month >= dateFrom.slice(0, 7) && p.month <= dateTo.slice(0, 7))
  const data = filtered.length > 0 ? filtered : trend

  const latest = data[data.length - 1]
  const previous = data.length > 1 ? data[data.length - 2] : latest

  const totalRevenue = data.reduce((sum, p) => sum + p.revenue, 0)
  const newUsersInRange = data.reduce((sum, p) => sum + p.newUsers, 0)

  const userGrowthPercent =
    previous.users > 0 ? ((latest.users - previous.users) / previous.users) * 100 : 0
  const revenueGrowthPercent =
    previous.revenue > 0 ? ((latest.revenue - previous.revenue) / previous.revenue) * 100 : 0

  return {
    totalUsers: latest.users,
    activeUsers: Math.round(latest.users * 0.87),
    newUsersInRange,
    totalRevenue,
    avgRevenuePerUser: latest.users > 0 ? Math.round(totalRevenue / data.length / latest.users) : 0,
    userGrowthPercent,
    revenueGrowthPercent,
  }
}

export const chartTypeOptions = [
  { value: 'bar' as const, label: 'Bar Chart' },
  { value: 'line' as const, label: 'Line Chart' },
  { value: 'pie' as const, label: 'Pie Chart' },
  { value: 'area' as const, label: 'Area Chart' },
  { value: 'none' as const, label: 'Hidden' },
]

export const visualizationLabels: Record<keyof ReportDisplayConfig, string> = {
  usersTrend: 'Users Over Time',
  revenueTrend: 'Revenue Over Time',
  usersByRole: 'Users by Role',
  revenueBySource: 'Revenue by Source',
  usersVsRevenue: 'Users vs Revenue Comparison',
}


