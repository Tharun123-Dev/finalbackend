import React from 'react';
import { usePermissions } from '@/auth/usePermissions';

export interface PermissionGateProps {
  permission?: string;
  permissions?: string[];
  requireAll?: boolean;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export function PermissionGate({
  permission,
  permissions,
  requireAll = false,
  fallback = null,
  children,
}: PermissionGateProps) {
  const { can, canAny, hasAllPermissions } = usePermissions();

  if (permission && !can(permission)) {
    return <>{fallback}</>;
  }

  if (permissions && permissions.length > 0) {
    if (requireAll) {
      if (!hasAllPermissions(permissions)) {
        return <>{fallback}</>;
      }
    } else {
      if (!canAny(permissions)) {
        return <>{fallback}</>;
      }
    }
  }

  return <>{children}</>;
}

export default PermissionGate;


