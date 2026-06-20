import rolesApi from './rolesApi';

export interface EmployeeOption {
  id: number;
  user_id: number;
  attendance_id?: string;
  emp_code: string;
  username: string;
  first_name: string;
  last_name: string;
  display_name: string;
  email: string;
  role: string;
  base_role?: string;
  employee_type: string;
  department?: number | null;
  department_name?: string | null;
  designation?: string | null;
  work_mode?: string | null;
  manager?: number | null;
  manager_name?: string | null;
  joining_date?: string | null;
}

const sortEmployees = (employees: EmployeeOption[]) =>
  [...employees].sort((a, b) => {
    const aName = a.display_name || a.username;
    const bName = b.display_name || b.username;
    return aName.localeCompare(bName);
  });

interface JavaUser {
  id?: number | string;
  userId?: number | string;
  user_id?: number | string;
  firstName?: string;
  first_name?: string;
  lastName?: string;
  last_name?: string;
  name?: string;
  username?: string;
  email?: string;
  active?: boolean;
  roleName?: string;
  role?: string;
  supervisorUserId?: number | string | null;
  supervisor_user_id?: number | string | null;
  reportingToUserId?: number | string | null;
  managerId?: number | string | null;
  supervisorName?: string | null;
  managerName?: string | null;
  employeeId?: string;
  emp_code?: string;
  profileData?: Record<string, unknown> | null;
}

// ─── Helpers ────────────────────────────────────────────────────────────────

const asArray = <T>(
  payload: T[] | { data?: T[]; content?: T[]; results?: T[] } | unknown
): T[] => {
  if (Array.isArray(payload)) return payload;
  if (payload && typeof payload === 'object') {
    const w = payload as { data?: T[]; content?: T[]; results?: T[] };
    return w.data || w.content || w.results || [];
  }
  return [];
};

const normalizeId = (value: unknown) => String(value ?? '').trim();

const normalizeRole = (value?: string | null) =>
  String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, '_');

const javaId = (user: JavaUser) =>
  normalizeId(user.id ?? user.userId ?? user.user_id);

const javaSupervisorId = (user: JavaUser) => {
  const p = user.profileData || {};
  return normalizeId(
    user.supervisorUserId ??
    user.supervisor_user_id ??
    user.reportingToUserId ??
    user.managerId ??
    p.reporting_supervisor_id ??
    p.reportingSupervisorId ??
    p.supervisorUserId ??
    p.managerId
  );
};

const baseRoleFromJavaRole = (value?: string | null): string => {
  const role = normalizeRole(value);
  if (!role) return 'employee';
  if (role.includes('super') && role.includes('admin')) return 'superadmin';
  if (role.includes('admin')) return 'admin';
  if (role.includes('hr') || role.includes('human_resource')) return 'hr';
  if (role.includes('manager') || role.includes('head') || role.includes('director')) return 'manager';
  if (role.includes('lead') || role.includes('leader') || role.includes('tl')) return 'tl';
  if (role.includes('counsel')) return 'counselor';
  return 'employee';
};

/**
 * All IDs that can be considered "me"
 * (covers camelCase / snake_case / JWT variants).
 */
const currentUserIds = (me: JavaUser | null): Set<string> => {
  const ids = new Set<string>();
  if (me) {
    [me.id, me.userId, me.user_id].forEach((v) => ids.add(normalizeId(v)));
  }
  try {
    const token = localStorage.getItem('token');
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]));
      [payload.id, payload.userId, payload.user_id, payload.sub].forEach((v) =>
        ids.add(normalizeId(v))
      );
    }
  } catch {
    // Ignore malformed tokens
  }
  return new Set(Array.from(ids).filter(Boolean));
};

// ─── Core: build full reporting subtree for ANY user ────────────────────────

/**
 * BFS walk DOWN the supervisor → subordinate tree starting from `rootIds`.
 *
 * Returns every active user whose supervisor chain leads back to one of the
 * root IDs — regardless of THEIR role or the CURRENT USER's role.
 *
 * This is the single generic function that powers all role-based filtering:
 *   - Employee   sees only their own direct/indirect reports
 *   - TL         sees their direct/indirect reports
 *   - Manager    sees their direct/indirect reports
 *   - HR         sees their direct/indirect reports
 *   - SuperAdmin sees their direct/indirect reports
 *
 * No special-casing per role. The tree structure decides visibility.
 */
const buildReportingSubtree = (
  allActive: JavaUser[],
  rootIds: Set<string>
): JavaUser[] => {
  const visible = new Set<string>();
  let frontier = Array.from(rootIds);

  while (frontier.length) {
    const next: string[] = [];
    allActive.forEach((user) => {
      const id = javaId(user);
      const supId = javaSupervisorId(user);
      if (supId && frontier.includes(supId) && !visible.has(id)) {
        visible.add(id);
        next.push(id);
      }
    });
    frontier = next;
  }

  return allActive.filter((u) => visible.has(javaId(u)));
};

// ─── Dedup & transform ───────────────────────────────────────────────────────

const dedupeJavaUsers = (users: JavaUser[]): JavaUser[] => {
  const seen = new Set<string>();
  return users.filter((user) => {
    const id = javaId(user);
    const email = normalizeId(user.email || user.username).toLowerCase();
    const key = id ? `id:${id}` : `email:${email}`;
    if (!key || key === 'email:' || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
};

const javaUserToEmployee = (user: JavaUser): EmployeeOption => {
  const p = user.profileData || {};
  const id = javaId(user);
  const firstName = user.firstName || user.first_name || '';
  const lastName = user.lastName || user.last_name || '';
  const username = user.username || user.email || `user-${id}`;
  const displayName = `${firstName} ${lastName}`.trim() || user.name || username;
  const role = user.roleName || user.role || 'Employee';
  const empCode =
    user.employeeId ||
    user.emp_code ||
    String(p.emp_code || p.employeeId || p.employee_id || `USR-${id}`);

  const attendanceId = [
    'java',
    id,
    encodeURIComponent(user.email || ''),
    encodeURIComponent(role),
    encodeURIComponent(firstName),
    encodeURIComponent(lastName),
    encodeURIComponent(empCode),
  ].join(':');

  return {
    id: Number(id) || 0,
    user_id: Number(id) || 0,
    attendance_id: attendanceId,
    emp_code: empCode,
    username,
    first_name: firstName,
    last_name: lastName,
    display_name: displayName,
    email: user.email || '',
    role,
    base_role: baseRoleFromJavaRole(role),
    employee_type: String(p.employee_type || p.employeeType || 'regular'),
    department: p.department_id ? Number(p.department_id) : null,
    department_name: p.department_name ? String(p.department_name) : null,
    designation: p.designation ? String(p.designation) : null,
    work_mode: p.work_mode ? String(p.work_mode) : null,
    manager: Number(javaSupervisorId(user)) || null,
    manager_name:
      user.supervisorName ||
      user.managerName ||
      String(p.reporting_supervisor_name || p.reportingSupervisorName || '') ||
      null,
    joining_date: String(p.joining_date || p.joiningDate || ''),
  };
};

const mergeEmployees = (
  lapEmployees: EmployeeOption[],
  javaUsers: JavaUser[]
): EmployeeOption[] => {
  const merged = new Map<string, EmployeeOption>();
  lapEmployees.forEach((emp) => {
    const key = emp.email ? `email:${emp.email.toLowerCase()}` : `id:${emp.user_id}`;
    merged.set(key, emp);
  });
  javaUsers.forEach((user) => {
    const emp = javaUserToEmployee(user);
    const key = emp.email ? `email:${emp.email.toLowerCase()}` : `java:${javaId(user)}`;
    const existing = merged.get(key);
    merged.set(key, {
      ...emp,
      ...(existing || {}),
      attendance_id: existing?.attendance_id || emp.attendance_id,
      manager: existing?.manager ?? emp.manager,
      manager_name: existing?.manager_name ?? emp.manager_name,
      role: existing?.role || emp.role,
      base_role: existing?.base_role || emp.base_role,
      joining_date: existing?.joining_date || emp.joining_date,
    });
  });
  return sortEmployees(Array.from(merged.values()));
};

// ─── Service ─────────────────────────────────────────────────────────────────

export const employeeService = {
  /**
   * List employees with **dynamic reporting-tree scoping**.
   *
   * Rule (applies to EVERY role — Employee, TL, Manager, HR, SuperAdmin):
   *   • No filter active  → show all active users (original behaviour)
   *   • role filter OR reportingOnly=true → show ONLY users from
   *     the current user's reporting subtree, then apply the role filter
   *
   * Examples:
   *   hr1 hr1 calls list({ role: 'EMPLOYEE' })
   *     → returns only Employees who report (directly/indirectly) to hr1
   *
   *   manager calls list({ role: 'TEAM LEADERS' })
   *     → returns only TLs who report (directly/indirectly) to manager
   *
   *   tl1 calls list({ role: 'EMPLOYEE' })
   *     → returns only Employees who report (directly/indirectly) to tl1
   *
   * @param params.role          Role label to filter by (e.g. 'EMPLOYEE', 'TEAM LEADERS', 'HR')
   * @param params.reportingOnly Scope to reporting subtree even without a role filter
   * @param params.department    Optional department filter
   * @param params.search        Optional name/email search
   * @param params.active        Optional active-status filter
   */
  list: async (
    params: {
      role?: string;
      department?: string;
      active?: boolean;
      search?: string;
      /** When true, restricts results to current user's reporting subtree */
      reportingOnly?: boolean;
    } = {}
  ) => {
    const { reportingOnly, ...apiParams } = params;

    // 1. Resolve current user identity
    const meRes = await rolesApi
      .get<JavaUser>('/users/me', { ignore403: true })
      .catch(() => ({ data: null as JavaUser | null }));
    const me = meRes.data || null;
    const myIds = currentUserIds(me);

    // 2. Fetch LAP employees + Java users in parallel
    const [lapRes, usersRes] = await Promise.all([
      rolesApi
        .get<EmployeeOption[]>('/employees/', { params: apiParams, ignore403: true })
        .catch(() => ({ data: [] as EmployeeOption[] })),
      rolesApi
        .get<JavaUser[] | { data?: JavaUser[]; content?: JavaUser[]; results?: JavaUser[] }>(
          '/users',
          { params: { search: apiParams.search || undefined }, ignore403: true }
        )
        .catch(() => ({ data: [] as JavaUser[] })),
    ]);

    // 3. Dedupe and keep only active users
    const allActive = dedupeJavaUsers(asArray<JavaUser>(usersRes.data)).filter(
      (u) => u.active !== false && javaId(u)
    );

    // 4. Dynamic scoping decision:
    //    role filter present OR reportingOnly=true
    //      → scope to reporting subtree of the current user (ALL roles treated equally)
    //    no filter
    //      → return all active users
    const shouldScopeToReports = !!(apiParams.role || reportingOnly);

    const scopedUsers = shouldScopeToReports
      ? buildReportingSubtree(allActive, myIds)
      : allActive;

    // 5. Apply role filter on the scoped list (client-side match)
    //    Matches raw role string OR derived base_role, both normalized.
    //    e.g. 'TEAM LEADERS' → normalizes to 'team_leaders' → matches base 'tl'
    const roleFilter = normalizeRole(apiParams.role);
    const filtered = roleFilter
      ? scopedUsers.filter((user) => {
          const raw = normalizeRole(user.roleName || user.role);
          const base = baseRoleFromJavaRole(user.roleName || user.role);
          return raw.includes(roleFilter) || base === roleFilter || raw === roleFilter;
        })
      : scopedUsers;

    // 6. Transform and return
    const javaEmployees = filtered.map(javaUserToEmployee);

    return {
      ...lapRes,
      data: javaEmployees.length
        ? sortEmployees(javaEmployees)
        : mergeEmployees(lapRes.data || [], []),
    };
  },
};