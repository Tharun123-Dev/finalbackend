import { Users, IndianRupee } from 'lucide-react'
import type { ReportFilters, ReportMetric } from '@/types/reports'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'

interface ReportFiltersBarProps {
  filters: ReportFilters
  onChange: (patch: Partial<ReportFilters>) => void
  onToggleMetric: (metric: ReportMetric) => void
}

export function ReportFiltersBar({ filters, onChange, onToggleMetric }: ReportFiltersBarProps) {
  return (
    <Card>
      <CardContent className="space-y-4 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-muted-foreground mr-1">Metrics:</span>
          {(
            [
              { id: 'users' as const, label: 'Users', icon: Users },
              { id: 'revenue' as const, label: 'Revenue', icon: IndianRupee },
            ] as const
          ).map(({ id, label, icon: Icon }) => {
            const active = filters.metrics.includes(id)
            return (
              <button
                key={id}
                type="button"
                onClick={() => onToggleMetric(id)}
                className={cn(
                  'inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm font-medium transition-all',
                  active
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border bg-card text-muted-foreground hover:bg-accent'
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            )
          })}
        </div>

        <div className="flex flex-wrap gap-3 items-end">
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Report type</label>
            <Select value={filters.reportType} onValueChange={(v) => onChange({ reportType: v })}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Report type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="analytics">Analytics</SelectItem>
                <SelectItem value="users">Users</SelectItem>
                <SelectItem value="revenue">Revenue</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">From</label>
            <Input
              type="date"
              className="w-[160px]"
              value={filters.dateFrom}
              onChange={(e) => onChange({ dateFrom: e.target.value })}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">To</label>
            <Input
              type="date"
              className="w-[160px]"
              value={filters.dateTo}
              onChange={(e) => onChange({ dateTo: e.target.value })}
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Branch</label>
            <Select value={filters.branchId} onValueChange={(v) => onChange({ branchId: v })}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Branch" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Branches</SelectItem>
                <SelectItem value="branch_hq">Head Office</SelectItem>
                <SelectItem value="branch_del">Delhi Branch</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}


