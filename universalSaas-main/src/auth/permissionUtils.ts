import { User } from './AuthContext';

const permissionAliases: Record<string, string[]> = {};

export function hasPermission(permissions: string[] | null, permissionKey: string): boolean {
  if (!permissions || !Array.isArray(permissions)) return false;
  if (!permissionKey || typeof permissionKey !== 'string') return false;
  
  const upperKey = permissionKey.toUpperCase();
  const upperPerms = permissions.map(p => String(p).toUpperCase());
  const normalizedKey = upperKey.replace(/[^A-Z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  const normalizedPerms = upperPerms.map(p => p.replace(/[^A-Z0-9*]+/g, '_').replace(/^_+|_+$/g, ''));

  // Global wildcard
  if (upperPerms.includes('*') || normalizedPerms.includes('*')) return true;

  // Exact match
  if (upperPerms.includes(upperKey) || normalizedPerms.includes(normalizedKey)) return true;

  const aliases = permissionAliases[normalizedKey] || [];
  if (aliases.some(alias => normalizedPerms.includes(alias))) return true;

  const parts = normalizedKey.split('_').filter(Boolean);
  if (parts.length >= 2) {
    const first = parts[0];
    const rest = parts.slice(1).join('_');
    const flipped = `${rest}_${first}`;
    if (normalizedPerms.includes(flipped)) return true;
  }

  // Namespace wildcard checks (e.g. USER_* matches USER_VIEW)
  for (const perm of normalizedPerms) {
    if (perm.endsWith('*')) {
      const prefix = perm.slice(0, -1);
      if (normalizedKey.startsWith(prefix)) {
        return true;
      }
    }
  }

  // Generic fallback: If the route requires a VIEW permission,
  // grant access if the user has CREATE, UPDATE, DELETE, or MANAGE permission for that entity.
  if (normalizedKey.endsWith('_VIEW')) {
    const prefix = normalizedKey.substring(0, normalizedKey.length - 5);
    const fallbackKeys = [
      `${prefix}_CREATE`,
      `${prefix}_UPDATE`,
      `${prefix}_DELETE`,
      `${prefix}_MANAGE`,
      `${prefix}_WRITE`
    ];
    if (fallbackKeys.some(key => normalizedPerms.includes(key))) {
      return true;
    }
  }

  return false;
}

export function hasAnyPermission(permissions: string[] | null, keys: string[]): boolean {
  if (!permissions || !Array.isArray(permissions)) return false;
  return keys.some(key => hasPermission(permissions, key));
}

export function hasAllPermissions(permissions: string[] | null, keys: string[]): boolean {
  if (!permissions || !Array.isArray(permissions)) return false;
  return keys.every(key => hasPermission(permissions, key));
}

export function isPlatformAdmin(user: User | null): boolean {
  return !!(user && user.isPlatformAdmin);
}


