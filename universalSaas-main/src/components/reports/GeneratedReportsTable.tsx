import { motion } from 'framer-motion'
import { Download, Users, IndianRupee, FileText, FileSpreadsheet } from 'lucide-react'
import type { GeneratedReport } from '@/types/reports'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

interface GeneratedReportsTableProps {
  reports: GeneratedReport[]
  generating?: boolean
  onGenerate: () => void
  onDownload: (report: GeneratedReport, format: 'json' | 'csv' | 'pdf') => void
}

export function GeneratedReportsTable({
  reports,
  generating,
  onGenerate,
  onDownload,
}: GeneratedReportsTableProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base">Generated Reports</CardTitle>
        <Button size="sm" onClick={onGenerate} disabled={generating}>
          {generating ? 'Generating…' : 'Generate Report'}
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">ID</th>
                <th className="px-4 py-3 text-left font-medium">Report</th>
                <th className="px-4 py-3 text-left font-medium">Type</th>
                <th className="px-4 py-3 text-left font-medium">Metrics</th>
                <th className="px-4 py-3 text-left font-medium">Date</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {reports.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-muted-foreground">
                    No reports match your filters. Adjust filters or generate a new report.
                  </td>
                </tr>
              ) : (
                reports.map((r, i) => (
                  <motion.tr
                    key={r.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.04 }}
                    className="border-b border-border hover:bg-muted/30"
                  >
                    <td className="px-4 py-3 font-mono text-xs">{r.id}</td>
                    <td className="px-4 py-3 font-medium">{r.name}</td>
                    <td className="px-4 py-3">{r.type}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        {r.metrics.includes('users') && (
                          <Badge variant="outline" className="gap-1">
                            <Users className="h-3 w-3" />
                            Users
                          </Badge>
                        )}
                        {r.metrics.includes('revenue') && (
                          <Badge variant="outline" className="gap-1">
                            <IndianRupee className="h-3 w-3" />
                            Revenue
                          </Badge>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{r.date}</td>
                    <td className="px-4 py-3">
                      <Badge
                        variant={
                          r.status === 'Ready' ? 'success' : r.status === 'Failed' ? 'destructive' : 'warning'
                        }
                      >
                        {r.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="gap-1">
                            <Download className="h-3.5 w-3.5" />
                            Download
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => onDownload(r, 'pdf')}>
                            <FileText className="h-4 w-4" />
                            PDF (Print)
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => onDownload(r, 'csv')}>
                            <FileSpreadsheet className="h-4 w-4" />
                            CSV
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => onDownload(r, 'json')}>
                            <FileText className="h-4 w-4" />
                            JSON
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}


