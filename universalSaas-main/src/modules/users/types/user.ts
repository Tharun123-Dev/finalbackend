// src/modules/users/types/user.ts
export interface User {
  id: string;
  avatarUrl?: string;
  employeeId: string;
  firstName: string;
  lastName: string;
  email: string;
  phone?: string;
  role: string;
  department?: string;
  status: 'active' | 'inactive' | 'suspended';
  lastLogin?: string; // ISO string
  // Added for UI status display
  isActive: boolean;
}


