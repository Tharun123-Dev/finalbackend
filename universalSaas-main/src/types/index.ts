import type { LucideIcon } from 'lucide-react'

export type Permission = string

export interface TenantContext {
  companyId: string
  companyName: string
  branchId: string
  branchName: string
  role: string
  userName: string
  userEmail: string
  avatarUrl?: string
}

export interface NavItem {
  id: string
  label: string
  path: string
  icon: LucideIcon
  badge?: number
  permissions?: Permission[]
  module?: string
  children?: NavItem[]
}

export interface NavSection {
  id: string
  label: string
  items: NavItem[]
  permissions?: Permission[]
  module?: string
}

export interface ModuleDefinition {
  id: string
  name: string
  slug: string
  enabled: boolean
  permissions: Permission[]
}

export interface StatWidget {
  id: string
  title: string
  value: string | number
  change: number
  trend: 'up' | 'down'
  icon: LucideIcon
  gradient: string
}

export interface ActivityItem {
  id: string
  type: 'followup' | 'user' | 'task' | 'attendance' | 'ticket' | 'revenue'
  title: string
  description: string
  timestamp: string
  user: string
  status?: 'success' | 'warning' | 'error' | 'info'
}

export interface Integration {
  id: string
  name: string
  description: string
  connected: boolean
  enabled: boolean
  lastSynced?: string
  health: 'healthy' | 'warning' | 'error'
  color: string
}

