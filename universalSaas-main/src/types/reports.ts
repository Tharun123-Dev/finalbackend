export type ChartType = 'bar' | 'line' | 'pie' | 'area' | 'none'

export type ReportMetric = 'users' | 'revenue'

export interface ChartVisualizationSetting {
  enabled: boolean
  chartType: ChartType
}

export interface ReportDisplayConfig {
  usersTrend: ChartVisualizationSetting
  revenueTrend: ChartVisualizationSetting
  usersByRole: ChartVisualizationSetting
  revenueBySource: ChartVisualizationSetting
  usersVsRevenue: ChartVisualizationSetting
}

export interface ReportFilters {
  dateFrom: string
  dateTo: string
  branchId: string
  reportType: string
  metrics: ReportMetric[]
}

export interface MonthlyTrendPoint {
  month: string
  label: string
  users: number
  newUsers: number
  revenue: number
  growth: number
}

export interface BreakdownPoint {
  name: string
  value: number
  color: string
}

export interface GeneratedReport {
  id: string
  name: string
  type: string
  metrics: ReportMetric[]
  date: string
  status: 'Ready' | 'Processing' | 'Failed'
  branchId: string
}

export interface ReportSummary {
  totalUsers: number
  activeUsers: number
  newUsersInRange: number
  totalRevenue: number
  avgRevenuePerUser: number
  userGrowthPercent: number
  revenueGrowthPercent: number
}

