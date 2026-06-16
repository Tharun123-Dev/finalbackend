import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  CalendarCheck,
  UserPlus,
  CheckSquare,
  Clock,
  Headphones,
  IndianRupee,
  ArrowRight,
} from 'lucide-react'
import type { ActivityItem } from '@/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { useToast } from '@/context/ToastContext'
import { cn } from '@/lib/utils'

const typeIcons = {
  followup: CalendarCheck,
  user: UserPlus,
  task: CheckSquare,
  attendance: Clock,
  ticket: Headphones,
  revenue: IndianRupee,
}

const typeRoutes: Partial<Record<ActivityItem['type'], string>> = {
  followup: '/followups',
  user: '/users',
  task: '/tasks',
  attendance: '/attendance',
  ticket: '/tickets',
  revenue: '/revenue',
}

const statusColors = {
  success: 'bg-emerald-500',
  warning: 'bg-amber-500',
  error: 'bg-red-500',
  info: 'bg-blue-500',
}

interface ActivityTimelineProps {
  activities: ActivityItem[]
}

export function ActivityTimeline({ activities }: ActivityTimelineProps) {
  const navigate = useNavigate()
  const { info } = useToast()

  const openActivity = (item: ActivityItem) => {
    const route = typeRoutes[item.type]
    if (route) {
      info('Opening activity', item.title)
      navigate(route)
    }
  }

  return (
    <Card className="shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Activity</CardTitle>
        <Button
          variant="ghost"
          size="sm"
          className="gap-1 text-xs"
          onClick={() => navigate('/reports')}
        >
          View all
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </CardHeader>
      <CardContent>
        <div className="relative space-y-0">
          <div className="absolute left-[19px] top-2 bottom-2 w-px bg-border" />
          {activities.map((item, i) => {
            const Icon = typeIcons[item.type]
            return (
              <motion.button
                key={item.id}
                type="button"
                onClick={() => openActivity(item)}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.06 }}
                className="relative flex w-full gap-4 pb-6 text-left last:pb-0 rounded-lg hover:bg-muted/40 -mx-2 px-2 transition-colors"
              >
                <div className="relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-border bg-card shadow-sm">
                  <Icon className="h-4 w-4 text-primary" />
                  {item.status && (
                    <span
                      className={cn(
                        'absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full ring-2 ring-card',
                        statusColors[item.status]
                      )}
                    />
                  )}
                </div>
                <div className="min-w-0 flex-1 pt-0.5">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium">{item.title}</p>
                    <span className="shrink-0 text-xs text-muted-foreground">{item.timestamp}</span>
                  </div>
                  <p className="mt-0.5 text-sm text-muted-foreground">{item.description}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <Avatar className="h-6 w-6">
                      <AvatarFallback className="text-[10px]">
                        {item.user.slice(0, 2).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <span className="text-xs text-muted-foreground">{item.user}</span>
                  </div>
                </div>
              </motion.button>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
/// Ajay
/// vinay
//tharun

