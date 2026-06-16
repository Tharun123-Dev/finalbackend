import { motion } from 'framer-motion'
import { Settings2, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import type { IntegrationCardResponse } from '@/types/integrations-api'
import { integrationColor, normalizeHealth } from '@/config/integration-meta'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface IntegrationCardProps {
  integration: IntegrationCardResponse
  index: number
  selected: boolean
  toggling: boolean
  onSelect: () => void
  onToggle: (enabled: boolean) => void
}

export function IntegrationCard({
  integration,
  index,
  selected,
  toggling,
  onSelect,
  onToggle,
}: IntegrationCardProps) {
  const health = normalizeHealth(integration.health)
  const color = integrationColor(integration.code, integration.color)

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Card
        className={cn(
          'cursor-pointer transition-all hover:shadow-md',
          selected && 'ring-2 ring-primary'
        )}
        onClick={onSelect}
      >
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div
              className="flex h-12 w-12 items-center justify-center rounded-xl text-lg font-bold text-white"
              style={{ backgroundColor: color }}
            >
                          {integration.name?.[0] ?? ''}


            </div>
            <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
              {toggling && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
              <Switch
                checked={integration.enabled}
                disabled={toggling}
                onCheckedChange={onToggle}
              />
            </div>
          </div>
          <h3 className="mt-4 font-semibold">{integration.name}</h3>
          <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
            {integration.description}
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <Badge variant={integration.connected ? 'success' : 'secondary'}>
              {integration.connected ? 'Connected' : 'Disconnected'}
            </Badge>
            {health === 'healthy' ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            ) : (
              <AlertCircle
                className={cn(
                  'h-4 w-4',
                  health === 'error' ? 'text-red-500' : 'text-amber-500'
                )}
              />
            )}
            {integration.lastSynced && (
              <span className="text-xs text-muted-foreground">
                Synced {formatSynced(integration.lastSynced)}
              </span>
            )}
          </div>
          <div className="flex justify-end mt-4">
          <Button
            variant="outline"
            size="sm"
            className="gap-2 whitespace-nowrap"
            onClick={(e) => {
              e.stopPropagation()
              onSelect()
            }}
          >
            <Settings2 className="h-4 w-4" />
            Configure
          </Button>
        </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

function formatSynced(value: string): string {
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleString()
}


