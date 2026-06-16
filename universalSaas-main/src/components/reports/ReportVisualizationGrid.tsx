import { BarChart3 } from 'lucide-react'
import type { ReportDisplayConfig } from '@/types/reports'
import type { MonthlyTrendPoint } from '@/types/reports'
import { visualizationLabels } from '@/config/reports-data'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  ReportBreakdownChart,
  ReportCombinedChart,
  ReportTrendChart,
} from '@/components/reports/ReportChart'
import { usersByRole, revenueBySource } from '@/config/reports-data'

interface ReportVisualizationGridProps {
  config: ReportDisplayConfig
  trendData: MonthlyTrendPoint[]
  showUsers: boolean
  showRevenue: boolean
}

function ChartTypeBadge({ type }: { type: string }) {
  return (
    <Badge variant="secondary" className="text-[10px] capitalize font-normal">
      {type === 'none' ? 'hidden' : type}
    </Badge>
  )
}

export function ReportVisualizationGrid({
  config,
  trendData,
  showUsers,
  showRevenue,
}: ReportVisualizationGridProps) {
  const widgets: {
    key: keyof ReportDisplayConfig
    show: boolean
    title: string
    content: React.ReactNode
  }[] = [
    {
      key: 'usersTrend',
      show: showUsers && config.usersTrend.enabled && config.usersTrend.chartType !== 'none',
      title: visualizationLabels.usersTrend,
      content: (
        <ReportTrendChart
          chartType={config.usersTrend.chartType}
          data={trendData}
          dataKey="users"
          color="#6366f1"
        />
      ),
    },
    {
      key: 'revenueTrend',
      show: showRevenue && config.revenueTrend.enabled && config.revenueTrend.chartType !== 'none',
      title: visualizationLabels.revenueTrend,
      content: (
        <ReportTrendChart
          chartType={config.revenueTrend.chartType}
          data={trendData}
          dataKey="revenue"
          color="#10b981"
        />
      ),
    },
    {
      key: 'usersByRole',
      show: showUsers && config.usersByRole.enabled && config.usersByRole.chartType !== 'none',
      title: visualizationLabels.usersByRole,
      content: (
        <ReportBreakdownChart chartType={config.usersByRole.chartType} data={usersByRole} />
      ),
    },
    {
      key: 'revenueBySource',
      show: showRevenue && config.revenueBySource.enabled && config.revenueBySource.chartType !== 'none',
      title: visualizationLabels.revenueBySource,
      content: (
        <ReportBreakdownChart chartType={config.revenueBySource.chartType} data={revenueBySource} />
      ),
    },
    {
      key: 'usersVsRevenue',
      show:
        (showUsers || showRevenue) &&
        config.usersVsRevenue.enabled &&
        config.usersVsRevenue.chartType !== 'none',
      title: visualizationLabels.usersVsRevenue,
      content: (
        <ReportCombinedChart
          chartType={config.usersVsRevenue.chartType}
          data={trendData}
          showUsers={showUsers}
          showRevenue={showRevenue}
        />
      ),
    },
  ]

  const visible = widgets.filter((w) => w.show)

  if (visible.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-16 text-center">
          <BarChart3 className="h-12 w-12 text-muted-foreground/40" />
          <p className="mt-4 font-medium text-muted-foreground">No charts visible</p>
          <p className="mt-1 text-sm text-muted-foreground max-w-sm">
            Select Users and/or Revenue metrics, or ask an admin to enable chart widgets in display settings.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {visible.map((widget) => {
        const setting = config[widget.key]
        return (
          <Card
            key={widget.key}
            className={widget.key === 'usersVsRevenue' ? 'lg:col-span-2' : undefined}
          >
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-base">{widget.title}</CardTitle>
              <ChartTypeBadge type={setting.chartType} />
            </CardHeader>
            <CardContent>{widget.content}</CardContent>
          </Card>
        )
      })}
    </div>
  )
}


