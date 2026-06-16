// src/services/userService.ts
// Mock service for fetching users. In a real app replace with actual API calls.

interface GetUsersParams {
  q?: string; // search query
  page?: number;
  limit?: number;
}

interface User {
  id: string;
  avatarUrl: string;
  employeeId: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  role: string;
  department: string;
  isActive: boolean;
  lastLogin: string;
}

interface GetUsersResponse {
  data: User[];
  total: number;
}

export async function getUsers(params: GetUsersParams = {}): Promise<GetUsersResponse> {
  // This mock returns a static list; replace with real fetch logic.
  const mockUsers: User[] = [
    {
      id: "1",
      avatarUrl: "https://i.pravatar.cc/40?img=1",
      employeeId: "EMP001",
      firstName: "Alice",
      lastName: "Smith",
      email: "alice.smith@example.com",
      phone: "555-0101",
      role: "admin",
      department: "Engineering",
      isActive: true,
      lastLogin: new Date().toISOString(),
    },
    {
      id: "2",
      avatarUrl: "https://i.pravatar.cc/40?img=2",
      employeeId: "EMP002",
      firstName: "Bob",
      lastName: "Johnson",
      email: "bob.johnson@example.com",
      phone: "555-0202",
      role: "manager",
      department: "Sales",
      isActive: false,
      lastLogin: new Date().toISOString(),
    },
  ];

  // Simple client‑side pagination and filter
  const { q = "", page = 1, limit = 10 } = params;
  const filtered = mockUsers.filter((u) =>
    `${u.firstName} ${u.lastName}`.toLowerCase().includes(q.toLowerCase())
  );
  const start = (page - 1) * limit;
  const paginated = filtered.slice(start, start + limit);

  return {
    data: paginated,
    total: filtered.length,
  };
}

