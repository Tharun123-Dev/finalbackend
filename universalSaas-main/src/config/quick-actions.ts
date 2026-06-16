import type { LucideIcon } from 'lucide-react'
import {
  Users,
  UserPlus,
  ListTodo,
  Wallet,
  Headphones,
  BarChart3,
  Megaphone,
  TrendingUp,
} from 'lucide-react'

export type QuickActionId =
  | 'add-user'
  | 'add-lead'
  | 'create-task'
  | 'payroll'
  | 'ticket'
  | 'report'
  | 'announce'
  | 'followup'

export interface QuickActionDefinition {
  id: QuickActionId
  label: string
  icon: LucideIcon
  color: string
  /** Opens a form dialog; false = navigate or instant action */
  hasDialog: boolean
  navigateTo?: string
}

export const quickActionDefinitions: QuickActionDefinition[] = [
  { id: 'add-user', label: 'Add User', icon: Users, color: 'from-blue-500 to-indigo-600', hasDialog: false, navigateTo: '/users/create' },
  { id: 'add-lead', label: 'Add Lead', icon: UserPlus, color: 'from-violet-500 to-purple-600', hasDialog: true },
  { id: 'create-task', label: 'Create Task', icon: ListTodo, color: 'from-emerald-500 to-teal-600', hasDialog: true },
  { id: 'payroll', label: 'Generate Payroll', icon: Wallet, color: 'from-amber-500 to-orange-600', hasDialog: false, navigateTo: '/payroll' },
  { id: 'ticket', label: 'Create Ticket', icon: Headphones, color: 'from-rose-500 to-pink-600', hasDialog: true },
  { id: 'report', label: 'Generate Report', icon: BarChart3, color: 'from-cyan-500 to-blue-600', hasDialog: false, navigateTo: '/reports' },
  { id: 'announce', label: 'Send Announcement', icon: Megaphone, color: 'from-fuchsia-500 to-purple-600', hasDialog: true },
  { id: 'followup', label: 'Create Followup', icon: TrendingUp, color: 'from-slate-500 to-slate-700', hasDialog: true },
]

export const quickActionMap = Object.fromEntries(
  quickActionDefinitions.map((a) => [a.id, a])
) as Record<QuickActionId, QuickActionDefinition>


