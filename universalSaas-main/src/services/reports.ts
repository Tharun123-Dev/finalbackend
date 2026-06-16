/* eslint-disable @typescript-eslint/no-explicit-any */
import rolesApi from './rolesApi';


const API_BASE = import.meta.env.VITE_LAP_API_BASE || import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE || '/api';

export interface ReportsDashboardData {
  totals?: {
    employees: number;
    gross: number;
    net_pay: number;
    pf: number;
    tds: number;
    lop_deduction: number;
  };
  data?: any[];
  summary?: any[];
  working_days?: number;
}

export const reportsService = {
  getReportsDashboard: (params?: any) => rolesApi.get<ReportsDashboardData>('/reports/dashboard/', { params }),
  getAttendanceReport: (params?: any) => rolesApi.get<ReportsDashboardData>('/reports/attendance/', { params }),
  getLeaveReport: (params?: any) => rolesApi.get<ReportsDashboardData>('/reports/leave/', { params }),
  getPayrollReport: (params?: any) => rolesApi.get<ReportsDashboardData>('/reports/payroll/', { params }),
  getHeadcountReport: (params?: any) => rolesApi.get<ReportsDashboardData>('/reports/headcount/', { params }),
  getLopReport: (params?: any) => rolesApi.get<ReportsDashboardData>('/reports/lop/', { params }),
  getOvertimeReport: (params?: any) => rolesApi.get<ReportsDashboardData>('/reports/overtime/', { params }),
  downloadReportCsv: async (type: string, params: any) => {
    const cleanParams = Object.fromEntries(
      Object.entries({ ...params, format: 'csv' }).filter(([, v]) => v !== undefined && v !== null && v !== '')
    );
    const query = new URLSearchParams(cleanParams as any).toString();
    const url = `${API_BASE}/reports/${type}/?${query}`;
    const token = localStorage.getItem('token');
    const tenantCode = localStorage.getItem('tenantCode');

    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (tenantCode) headers['X-Tenant'] = tenantCode;

    try {
      const response = await fetch(url, { headers });
      const blob = await response.blob();
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `${type}_report.csv`;
      link.click();
      URL.revokeObjectURL(link.href);
    } catch (err) {
      console.error('CSV download error', err);
    }
  }
};

