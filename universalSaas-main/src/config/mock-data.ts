import { Users, UserPlus, IndianRupee, Headphones } from 'lucide-react'
import type { ActivityItem, Integration, StatWidget } from '@/types'

/** Primary KPIs shown on the main dashboard (full list available in module pages) */
export const dashboardStats: StatWidget[] = [
  { id: 'users', title: 'Total Users', value: '2,847', change: 12.5, trend: 'up', icon: Users, gradient: 'from-blue-500 via-blue-600 to-indigo-700' },
  { id: 'leads', title: 'Active Leads', value: '486', change: 8.2, trend: 'up', icon: UserPlus, gradient: 'from-violet-500 via-purple-600 to-fuchsia-700' },
  { id: 'revenue', title: 'Monthly Revenue', value: '₹48.2L', change: 15.3, trend: 'up', icon: IndianRupee, gradient: 'from-emerald-500 via-green-600 to-teal-700' },
  { id: 'tickets', title: 'Open Tickets', value: '34', change: 3.1, trend: 'up', icon: Headphones, gradient: 'from-rose-500 via-pink-600 to-red-600' },
]

export const recentActivities: ActivityItem[] = [
  { id: '1', type: 'followup', title: 'Follow-up completed', description: 'Called Acme Corp regarding enterprise plan', timestamp: '10 min ago', user: 'Sarah Chen', status: 'success' },
  { id: '2', type: 'user', title: 'New user registered', description: 'Raj Patel joined as Sales Executive', timestamp: '25 min ago', user: 'System', status: 'info' },
  { id: '3', type: 'task', title: 'Task updated', description: 'Q2 Marketing Campaign marked as In Progress', timestamp: '1 hr ago', user: 'Mike Johnson', status: 'warning' },
  { id: '4', type: 'attendance', title: 'Attendance logged', description: 'Team Alpha — 42/45 present today', timestamp: '2 hrs ago', user: 'HR System', status: 'success' },
  { id: '5', type: 'ticket', title: 'Ticket escalated', description: '#TK-2847 — API integration issue', timestamp: '3 hrs ago', user: 'Support Bot', status: 'error' },
  { id: '6', type: 'revenue', title: 'Payment received', description: '₹2,45,000 from GlobalTech Solutions', timestamp: '4 hrs ago', user: 'Finance', status: 'success' },
]

export const revenueMonthly = [
  { month: 'Jan', revenue: 3200000, growth: 12 },
  { month: 'Feb', revenue: 3800000, growth: 18 },
  { month: 'Mar', revenue: 3500000, growth: 8 },
  { month: 'Apr', revenue: 4200000, growth: 20 },
  { month: 'May', revenue: 4100000, growth: 15 },
  { month: 'Jun', revenue: 4820000, growth: 22 },
]

export const leadsFunnel = [
  { stage: 'Visitors', count: 12500 },
  { stage: 'Leads', count: 3200 },
  { stage: 'Qualified', count: 890 },
  { stage: 'Proposal', count: 340 },
  { stage: 'Won', count: 128 },
]

export const conversionData = [
  { name: 'Won', value: 28, color: '#10b981' },
  { name: 'Lost', value: 22, color: '#ef4444' },
  { name: 'In Progress', value: 50, color: '#6366f1' },
]

export const attendanceWeekly = [
  { day: 'Mon', present: 42, late: 3 },
  { day: 'Tue', present: 44, late: 2 },
  { day: 'Wed', present: 41, late: 5 },
  { day: 'Thu', present: 43, late: 2 },
  { day: 'Fri', present: 40, late: 4 },
]

export const taskAnalytics = [
  { name: 'Completed', value: 342, color: '#10b981' },
  { name: 'Pending', value: 127, color: '#f59e0b' },
  { name: 'Overdue', value: 23, color: '#ef4444' },
]

export const integrations: Integration[] = [
  { id: 'google', name: 'Google Workspace', description: 'Calendar, Drive & Gmail sync', connected: true, enabled: true, lastSynced: '2 min ago', health: 'healthy', color: '#4285F4' },
  { id: 'whatsapp', name: 'WhatsApp Business', description: 'Customer messaging & notifications', connected: true, enabled: true, lastSynced: '5 min ago', health: 'healthy', color: '#25D366' },
  { id: 'meta', name: 'Meta (Facebook)', description: 'Ads & lead form integration', connected: false, enabled: false, health: 'warning', color: '#1877F2' },
  { id: 'zapier', name: 'Zapier', description: 'Workflow automation', connected: true, enabled: true, lastSynced: '1 hr ago', health: 'healthy', color: '#FF4A00' },
  { id: 'zoom', name: 'Zoom', description: 'Video meetings & webinars', connected: true, enabled: false, lastSynced: '3 hrs ago', health: 'warning', color: '#2D8CFF' },
  { id: 'cashfree', name: 'Cashfree', description: 'Payment gateway', connected: true, enabled: true, lastSynced: '30 sec ago', health: 'healthy', color: '#00C853' },
  { id: 'webhooks', name: 'Webhooks', description: 'Custom event endpoints', connected: true, enabled: true, lastSynced: 'Just now', health: 'healthy', color: '#6366f1' },
]


