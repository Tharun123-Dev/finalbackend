// src/modules/services/userService.ts
import type { User } from '../users/types/user';

interface GetUsersParams {
  q?: string;
  page: number;
  limit: number;
}

/**
 * Mock implementation of a user service.
 * Returns paginated mock user data.
 */
export async function getUsers({ q = '', page, limit }: GetUsersParams) {
  // Generate a pool of mock users
  const mockUsers: User[] = Array.from({ length: 50 }, (_, i) => ({
    id: String(i + 1),
    avatarUrl: `https://i.pravatar.cc/150?img=${(i % 70) + 1}`,
    employeeId: `EMP${1000 + i}`,
    firstName: `First${i}`,
    lastName: `Last${i}`,
    email: `user${i}@example.com`,
    phone: `+1-555-01${String(i).padStart(2, '0')}`,
    role: ['admin', 'manager', 'employee'][i % 3],
    department: ['HR', 'Engineering', 'Sales'][i % 3],
    status: i % 2 === 0 ? 'active' : 'inactive',
    isActive: i % 2 === 0,
    lastLogin: new Date(Date.now() - i * 86400000).toISOString(),
  }));

  // Filter by query (search in name or email)
  const filtered = mockUsers.filter(u =>
    u.firstName.toLowerCase().includes(q.toLowerCase()) ||
    u.lastName.toLowerCase().includes(q.toLowerCase()) ||
    u.email.toLowerCase().includes(q.toLowerCase())
  );

  const total = filtered.length;
  const start = (page - 1) * limit;
  const data = filtered.slice(start, start + limit);

  // Simulate async delay
  await new Promise(res => setTimeout(res, 150));
  return { data, total };
}


