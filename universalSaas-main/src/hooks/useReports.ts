import { useCallback, useMemo, useState } from 'react'
import { useToast } from '@/context/ToastContext'
import {
  DEFAULT_REPORT_DISPLAY_CONFIG,
  REPORT_DISPLAY_STORAGE_KEY,
  computeReportSummary,
  generatedReportsSeed,
  monthlyTrendData,
} from '@/config/reports-data'
import {
  exportExcelCsv,
  exportFullReportJson,
  exportReportJson,
  exportTrendCsv,
  printReportPdf,
} from '@/lib/report-export'
import type {
  GeneratedReport,
  ReportDisplayConfig,
  ReportFilters,
  ReportMetric,
} from '@/types/reports'

function loadDisplayConfig(): ReportDisplayConfig {
  try {
    const raw = localStorage.getItem(REPORT_DISPLAY_STORAGE_KEY)
    if (raw) return { ...DEFAULT_REPORT_DISPLAY_CONFIG, ...JSON.parse(raw) }
  } catch {
    /* use defaults */
  }
  return DEFAULT_REPORT_DISPLAY_CONFIG
}

const defaultFilters: ReportFilters = {
  dateFrom: '2026-01-01',
  dateTo: '2026-06-30',
  branchId: 'branch_hq',
  reportType: 'all',
  metrics: ['users', 'revenue'],
}

export function useReports(isAdmin: boolean) {
  const { success, info, error } = useToast()
  const [filters, setFilters] = useState<ReportFilters>(defaultFilters)

  const patchFilters = useCallback((patch: Partial<ReportFilters>) => {
    setFilters((prev) => ({ ...prev, ...patch }))
  }, [])
  const [displayConfig, setDisplayConfig] = useState<ReportDisplayConfig>(loadDisplayConfig)
  const [reports, setReports] = useState<GeneratedReport[]>(generatedReportsSeed)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [generating, setGenerating] = useState(false)

  const summary = useMemo(
    () => computeReportSummary(monthlyTrendData, filters.dateFrom, filters.dateTo),
    [filters.dateFrom, filters.dateTo]
  )

  const filteredTrend = useMemo(() => {
    return monthlyTrendData.filter(
      (p) => p.month >= filters.dateFrom.slice(0, 7) && p.month <= filters.dateTo.slice(0, 7)
    )
  }, [filters.dateFrom, filters.dateTo])

  const trendData = filteredTrend.length > 0 ? filteredTrend : monthlyTrendData

  const filteredReports = useMemo(() => {
    return reports.filter((r) => {
      if (filters.reportType !== 'all') {
        const typeMap: Record<string, string> = {
          analytics: 'Analytics',
          users: 'Users',
          revenue: 'Revenue',
        }
        if (r.type !== typeMap[filters.reportType]) return false
      }
      if (
        filters.branchId !== 'all' &&
        r.branchId !== 'all' &&
        r.branchId !== filters.branchId
      ) {
        return false
      }
      if (filters.metrics.length) {
        const hasOverlap = filters.metrics.some((m) => r.metrics.includes(m))
        if (!hasOverlap) return false
      }
      return true
    })
  }, [reports, filters])

  const updateDisplayConfig = useCallback(
    (key: keyof ReportDisplayConfig, patch: Partial<ReportDisplayConfig[keyof ReportDisplayConfig]>) => {
      if (!isAdmin) {
        error('Permission denied', 'Only admins can change chart display settings.')
        return
      }
      setDisplayConfig((prev) => {
        const next = { ...prev, [key]: { ...prev[key], ...patch } }
        localStorage.setItem(REPORT_DISPLAY_STORAGE_KEY, JSON.stringify(next))
        return next
      })
    },
    [isAdmin, error]
  )

  const resetDisplayConfig = useCallback(() => {
    if (!isAdmin) return
    setDisplayConfig(DEFAULT_REPORT_DISPLAY_CONFIG)
    localStorage.setItem(REPORT_DISPLAY_STORAGE_KEY, JSON.stringify(DEFAULT_REPORT_DISPLAY_CONFIG))
    success('Settings reset', 'Chart display restored to platform defaults.')
  }, [isAdmin, success])

  const saveDisplayConfig = useCallback(() => {
    if (!isAdmin) return
    localStorage.setItem(REPORT_DISPLAY_STORAGE_KEY, JSON.stringify(displayConfig))
    setSettingsOpen(false)
    success('Chart settings saved', 'Visualization preferences updated for all users.')
  }, [isAdmin, displayConfig, success])

  const toggleMetric = useCallback((metric: ReportMetric) => {
    setFilters((prev) => {
      const has = prev.metrics.includes(metric)
      const metrics = has
        ? prev.metrics.filter((m) => m !== metric)
        : [...prev.metrics, metric]
      return { ...prev, metrics: metrics.length ? metrics : [metric] }
    })
  }, [])

  const generateReport = useCallback(async () => {
    setGenerating(true)
    await new Promise((r) => setTimeout(r, 600))

    const id = `RPT-${String(reports.length + 1).padStart(3, '0')}`
    const name =
      filters.metrics.length === 2
        ? `Users & Revenue — ${new Date().toLocaleDateString('en-IN')}`
        : filters.metrics[0] === 'users'
          ? `User Report — ${new Date().toLocaleDateString('en-IN')}`
          : `Revenue Report — ${new Date().toLocaleDateString('en-IN')}`

    const newReport: GeneratedReport = {
      id,
      name,
      type:
        filters.metrics.length === 2
          ? 'Analytics'
          : filters.metrics[0] === 'users'
            ? 'Users'
            : 'Revenue',
      metrics: [...filters.metrics],
      date: new Date().toISOString().slice(0, 10),
      status: 'Ready',
      branchId: filters.branchId,
    }
    setReports((prev) => [newReport, ...prev])
    setGenerating(false)
    success('Report generated', `${id} is ready to download.`)
  }, [reports.length, filters, success])

  const downloadReport = useCallback(
    (report: GeneratedReport, format: 'json' | 'csv' | 'pdf') => {
      if (report.status === 'Processing') {
        info('Report processing', 'This report is still being generated. Try again shortly.')
        return
      }
      if (report.status === 'Failed') {
        error('Download failed', 'This report failed to generate. Please regenerate it.')
        return
      }

      switch (format) {
        case 'json':
          exportReportJson(report, summary, trendData, filters)
          success('Download started', `${report.id}.json`)
          break
        case 'csv':
          exportTrendCsv(trendData, `${report.id}.csv`)
          success('Download started', `${report.id}.csv`)
          break
        case 'pdf':
          printReportPdf(report, summary, trendData, filters)
          info('Opening print dialog', 'Save as PDF from the print dialog.')
          break
      }
    },
    [summary, trendData, filters, success, info, error]
  )

  const exportData = useCallback(
    (format: 'csv' | 'json' | 'excel' | 'pdf') => {
      switch (format) {
        case 'json':
          exportFullReportJson(filters, summary, trendData)
          success('Export complete', 'Full report JSON downloaded.')
          break
        case 'csv':
          exportTrendCsv(trendData, `report-export-${Date.now()}.csv`)
          success('Export complete', 'Trend data CSV downloaded.')
          break
        case 'excel':
          exportExcelCsv(trendData, `report-export-${Date.now()}.csv`)
          success('Export complete', 'Excel-compatible CSV downloaded.')
          break
        case 'pdf':
          printReportPdf(null, summary, trendData, filters)
          info('Print / PDF', 'Use Save as PDF in the print dialog.')
          break
      }
    },
    [filters, summary, trendData, success, info]
  )

  return {
    filters,
    setFilters,
    patchFilters,
    displayConfig,
    updateDisplayConfig,
    resetDisplayConfig,
    saveDisplayConfig,
    settingsOpen,
    setSettingsOpen,
    summary,
    trendData,
    filteredReports,
    toggleMetric,
    generateReport,
    generating,
    downloadReport,
    exportData,
    showUsers: filters.metrics.includes('users'),
    showRevenue: filters.metrics.includes('revenue'),
  }
}


