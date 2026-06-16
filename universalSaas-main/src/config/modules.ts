import type { ModuleDefinition } from '@/types'

export const platformModules: ModuleDefinition[] = [
  { id: 'hrms', name: 'HRMS', slug: 'hrms', enabled: true, permissions: ['hrms.view'] },
  { id: 'crm', name: 'CRM', slug: 'crm', enabled: true, permissions: ['crm.view'] },
  { id: 'lms', name: 'LMS', slug: 'lms', enabled: false, permissions: ['lms.view'] },
  { id: 'advocate', name: 'Advocate Management', slug: 'advocate', enabled: false, permissions: ['advocate.view'] },
  { id: 'temple', name: 'Temple Management', slug: 'temple', enabled: false, permissions: ['temple.view'] },
  { id: 'website', name: 'Website Builder', slug: 'website', enabled: true, permissions: ['website.view'] },
]

export function filterNavigationByPermissions<T extends { permissions?: string[] }>(
  items: T[],
  userPermissions: string[]
): T[] {
  return items.filter(
    (item) =>
      !item.permissions?.length ||
      item.permissions.some((p) => userPermissions.includes(p) || userPermissions.includes('*'))
  )
}


