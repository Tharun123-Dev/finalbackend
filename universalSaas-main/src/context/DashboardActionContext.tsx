/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { useNavigate } from 'react-router-dom'
import { useToast } from '@/context/ToastContext'
import type { QuickActionId } from '@/config/quick-actions'

interface DashboardActionContextValue {
  activeAction: QuickActionId | null
  openAction: (id: QuickActionId) => void
  closeAction: () => void
  runQuickAction: (id: QuickActionId) => void
}

const DashboardActionContext = createContext<DashboardActionContextValue | null>(null)

export function DashboardActionProvider({ children }: { children: ReactNode }) {
  const [activeAction, setActiveAction] = useState<QuickActionId | null>(null)
  const navigate = useNavigate()
  const { info } = useToast()

  const closeAction = useCallback(() => setActiveAction(null), [])

  const openAction = useCallback((id: QuickActionId) => setActiveAction(id), [])

  const runQuickAction = useCallback(
    (id: QuickActionId) => {
      switch (id) {
        case 'add-user':
          info('Adding User', 'Redirecting to user creation form…')
          navigate('/users/create')
          break
        case 'payroll':
          info('Opening Payroll', 'Redirecting to payroll module…')
          navigate('/payroll')
          break
        case 'report':
          info('Opening Reports', 'Redirecting to generate analytics…')
          navigate('/reports?action=generate')
          break
        default:
          openAction(id)
      }
    },
    [navigate, openAction, info]
  )

  const value = useMemo(
    () => ({ activeAction, openAction, closeAction, runQuickAction }),
    [activeAction, openAction, closeAction, runQuickAction]
  )

  return (
    <DashboardActionContext.Provider value={value}>{children}</DashboardActionContext.Provider>
  )
}

export function useDashboardActions() {
  const ctx = useContext(DashboardActionContext)
  if (!ctx) throw new Error('useDashboardActions must be used within DashboardActionProvider')
  return ctx
}


