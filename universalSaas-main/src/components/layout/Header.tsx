import { useLocation, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthContext'
import {
  Search,
  Bell,
  Sun,
  Moon,
  Plus,
  Menu,
  ChevronRight,
  Building2,
  GitBranch,
} from 'lucide-react'
import { useApp } from '@/context/AppContext'
import { useTheme } from '@/context/ThemeProvider'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'
import { DashboardQuickActionMenu } from '@/components/dashboard/DashboardQuickActionMenu'
import { useToast } from '@/context/ToastContext'
import { usePermissions } from '@/auth/usePermissions'

const pathLabels: Record<string, string> = {
  '/': 'Dashboard',
  '/users': 'Users',
  '/leads': 'Leads',
  '/reports': 'Reports',
  '/integrations': 'Integrations',
  '/messages': 'Messages',
  '/tickets': 'Support Tickets',
  '/attendance': 'Attendance',
  '/payroll': 'Payroll',
  '/settings': 'Settings',
  '/website': 'My Website',
  '/affiliate': 'Affiliate',
  '/vendor': 'Vendor',
}

export function Header() {
  const { tenant, sidebarCollapsed, setMobileSidebarOpen, setTenant } = useApp()
  const { theme, toggleTheme } = useTheme()
  const { info, success } = useToast()
  const { logout } = useAuth()
  const { hasAnyPermission } = usePermissions()
  const navigate = useNavigate()
  const location = useLocation()
  const showQuickActions = location.pathname === '/' || location.pathname === '/reports'
  const canUseQuickActions = hasAnyPermission([
    'USER_CREATE',
    'USER_CREATE',
    'LEADS_CREATE_LEAD',
    'LEADS_CREATE_LEAD',
    'TASKS_CREATE_TASK',
    'TASKS_EDIT_TASK',
    'PAYROLL_PROCESS_PAYROLL',
    'PAYROLL_PROCESS_PAYROLL',
    'SUPPORT_TICKETS_RAISE_SUPPORT_TICKET',
    'SUPPORT_TICKETS_RAISE_SUPPORT_TICKET',
    'REPORTS_VIEW_REPORTS',
    'REPORTS_VIEW_REPORTS',
    'ANNOUNCEMENT_CREATE',
    'NOTIFICATION_CREATE',
    'LEADS_CREATE_FOLLOWUP',
  ])
  const pageTitle = pathLabels[location.pathname] ?? 'Module'

  const initials = tenant.userName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .slice(0, 2)

  return (
    <header
      className={cn(
        'sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-card/80 px-4 backdrop-blur-md lg:px-6',
        sidebarCollapsed ? 'lg:pl-[88px]' : 'lg:pl-[272px]'
      )}
    >
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={() => setMobileSidebarOpen(true)}
      >
        <Menu className="h-5 w-5" />
      </Button>

      <nav className="hidden items-center gap-1 text-sm text-muted-foreground md:flex">
        <Link to="/" className="hover:text-foreground">
          Home
        </Link>
        <ChevronRight className="h-4 w-4" />
        <span className="font-medium text-foreground">{pageTitle}</span>
      </nav>

      <div className="relative ml-auto flex flex-1 items-center gap-2 sm:max-w-md lg:mx-4 lg:max-w-lg">
        <Search className="absolute left-3 h-4 w-4 text-muted-foreground" />
        <Input placeholder="Search modules, users, leads..." className="pl-9 bg-muted/50" />
      </div>

      <div className="hidden items-center gap-2 xl:flex">
        <Select
          value={tenant.companyId}
          onValueChange={(v) => {
            const names: Record<string, string> = {
              comp_001: 'Universal Enterprises',
              comp_002: 'Acme Holdings',
            }
            setTenant({ companyId: v, companyName: names[v] ?? tenant.companyName })
            success('Company switched', names[v])
          }}
        >
          <SelectTrigger className="h-9 w-[180px]">
            <Building2 className="mr-1 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="comp_001">Universal Enterprises</SelectItem>
            <SelectItem value="comp_002">Acme Holdings</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={tenant.branchId}
          onValueChange={(v) => {
            const names: Record<string, string> = {
              branch_hq: 'Head Office — Mumbai',
              branch_del: 'Delhi Branch',
            }
            setTenant({ branchId: v, branchName: names[v] ?? tenant.branchName })
            success('Branch switched', names[v])
          }}
        >
          <SelectTrigger className="h-9 w-[160px]">
            <GitBranch className="mr-1 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="branch_hq">Head Office</SelectItem>
            <SelectItem value="branch_del">Delhi Branch</SelectItem>
          </SelectContent>
        </Select>
        <span className="rounded-md bg-muted px-2 py-1 text-xs font-medium">{tenant.role}</span>
      </div>

      {canUseQuickActions && showQuickActions ? (
        <div className="hidden sm:block">
          <DashboardQuickActionMenu />
        </div>
      ) : canUseQuickActions ? (
        <Button
          size="sm"
          className="hidden gap-1 sm:flex shadow-md"
          onClick={() => {
            info('Quick Action', 'Navigate to Dashboard for quick actions.')
            navigate('/')
          }}
        >
          <Plus className="h-4 w-4" />
          Quick Action
        </Button>
      ) : null}

      <Button variant="ghost" size="icon" className="relative" onClick={toggleTheme}>
        {theme === 'light' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
      </Button>

      <Button
        variant="ghost"
        size="icon"
        className="relative"
        onClick={() => info('Notifications', 'You have 3 unread notifications.')}
      >
        <Bell className="h-5 w-5" />
        <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-500" />
      </Button>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button type="button" className="flex items-center gap-2 rounded-lg p-1 hover:bg-accent">
            <Avatar className="h-9 w-9">
              <AvatarFallback className="bg-gradient-to-br from-indigo-500 to-violet-600 text-white text-xs">
                {initials}
              </AvatarFallback>
            </Avatar>
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel>
            <p className="font-medium">{tenant.userName}</p>
            <p className="text-xs font-normal text-muted-foreground">{tenant.userEmail}</p>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => navigate('/settings')}>Profile</DropdownMenuItem>
          <DropdownMenuItem onClick={() => navigate('/settings')}>Preferences</DropdownMenuItem>
          <DropdownMenuItem onClick={() => info('Billing', 'Billing module coming soon.')}>Billing</DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="text-red-600"
            onClick={() => {
              logout();
              success('Signed out', 'You have been logged out.');
              navigate('/login');
            }}
          >
            Sign out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  )
}


