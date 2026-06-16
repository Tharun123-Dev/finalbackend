import type { GeneratedReport, ReportFilters, ReportSummary, MonthlyTrendPoint } from '@/types/reports'
import { formatCurrency } from '@/lib/utils'

export function downloadBlob(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function exportTrendCsv(trend: MonthlyTrendPoint[], filename: string) {
  const rows = [
    'month,label,users,newUsers,revenue,growth',
    ...trend.map((r) => `${r.month},${r.label},${r.users},${r.newUsers},${r.revenue},${r.growth}`),
  ]
  downloadBlob(rows.join('\n'), filename, 'text/csv')
}

export function exportReportJson(
  report: GeneratedReport,
  summary: ReportSummary,
  trend: MonthlyTrendPoint[],
  filters: ReportFilters
) {
  const payload = { report, summary, trend, filters, exportedAt: new Date().toISOString() }
  downloadBlob(JSON.stringify(payload, null, 2), `${report.id}.json`, 'application/json')
}

export function exportFullReportJson(
  filters: ReportFilters,
  summary: ReportSummary,
  trend: MonthlyTrendPoint[]
) {
  const payload = { filters, summary, trend, exportedAt: new Date().toISOString() }
  downloadBlob(JSON.stringify(payload, null, 2), `report-${Date.now()}.json`, 'application/json')
}

export function exportExcelCsv(trend: MonthlyTrendPoint[], filename: string) {
  exportTrendCsv(trend, filename.replace(/\.xlsx?$/i, '.csv'))
}

function buildPrintHtml(title: string, body: string) {
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>${title}</title>
  <style>
    body { font-family: Inter, system-ui, sans-serif; padding: 32px; color: #111; }
    h1 { font-size: 22px; margin-bottom: 8px; }
    .meta { color: #666; font-size: 12px; margin-bottom: 24px; }
    table { width: 100%; border-collapse: collapse; margin-top: 16px; }
    th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; font-size: 13px; }
    th { background: #f4f4f5; }
    .summary { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin: 20px 0; }
    .card { border: 1px solid #e4e4e7; border-radius: 8px; padding: 12px; }
    .card strong { display: block; font-size: 18px; margin-top: 4px; }
  </style>
</head>
<body>
  ${body}
  <script>window.onload = () => { window.print(); }</script>
</body>
</html>`
}

export function printReportPdf(
  report: GeneratedReport | null,
  summary: ReportSummary,
  trend: MonthlyTrendPoint[],
  filters: ReportFilters
) {
  const title = report?.name ?? 'Universal SaaS Report'
  const rows = trend
    .map(
      (r) =>
        `<tr><td>${r.label}</td><td>${r.users.toLocaleString()}</td><td>${r.newUsers}</td><td>${formatCurrency(r.revenue)}</td><td>${r.growth}%</td></tr>`
    )
    .join('')

  const body = `
    <h1>${title}</h1>
    <p class="meta">Generated ${new Date().toLocaleString()} · Branch: ${filters.branchId} · Period: ${filters.dateFrom} to ${filters.dateTo}</p>
    <div class="summary">
      <div class="card">Total Users<strong>${summary.totalUsers.toLocaleString()}</strong></div>
      <div class="card">Total Revenue<strong>${formatCurrency(summary.totalRevenue)}</strong></div>
      <div class="card">New Users<strong>${summary.newUsersInRange.toLocaleString()}</strong></div>
      <div class="card">Avg Rev/User<strong>${formatCurrency(summary.avgRevenuePerUser)}</strong></div>
    </div>
    <table>
      <thead><tr><th>Month</th><th>Users</th><th>New</th><th>Revenue</th><th>Growth</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `

  const win = window.open('', '_blank')
  if (!win) return
  win.document.write(buildPrintHtml(title, body))
  win.document.close()
}


