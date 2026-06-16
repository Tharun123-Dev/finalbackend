// /* eslint-disable react-hooks/set-state-in-effect */
// /* eslint-disable react-hooks/exhaustive-deps */
// import { useEffect, useState, useMemo, useCallback } from 'react';
// import { createPortal } from 'react-dom';
// import { MapPin, Clock, Loader2, CheckCircle2, AlertTriangle, RefreshCw, X } from 'lucide-react';
// import { PageHeader } from '@/components/shared/PageHeader';
// import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
// import { Badge } from '@/components/ui/badge';
// import { Button } from '@/components/ui/button';
// import { Input } from '@/components/ui/input';
// import { cn } from '@/lib/utils';
// import { usePermissions } from '@/auth/usePermissions';
// import { attendanceService, AttendanceRecord, AttendancePolicy, OfficeLocation, RegularizationRequest, Holiday } from '@/services/attendance';
// import toast from 'react-hot-toast';

// const STATUS_COLOR: Record<string, { bg: string; color: string; label: string; title: string }> = {
//   present: { bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-500', color: 'text-emerald-500', label: 'P', title: 'Present' },
//   late: { bg: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-500', color: 'text-yellow-500', label: 'L', title: 'Late' },
//   half_day: { bg: 'bg-amber-500/10 border-amber-500/30 text-amber-500', color: 'text-amber-500', label: 'H', title: 'Half Day' },
//   absent: { bg: 'bg-red-500/10 border-red-500/30 text-red-500', color: 'text-red-500', label: 'A', title: 'Absent / LOP' },
//   pending: { bg: 'bg-orange-500/10 border-orange-500/30 text-orange-500', color: 'text-orange-500', label: 'PEN', title: 'Pending Correction' },
//   missing: { bg: 'bg-slate-500/10 border-slate-500/30 text-slate-500', color: 'text-slate-500', label: 'M', title: 'Missing Punch' },
//   leave: { bg: 'bg-purple-500/10 border-purple-500/30 text-purple-500', color: 'text-purple-500', label: 'LV', title: 'On Leave' },
//   lop_leave: { bg: 'bg-rose-500/10 border-rose-500/30 text-rose-500', color: 'text-rose-500', label: 'LOP', title: 'LOP Leave' },
//   holiday: { bg: 'bg-blue-500/10 border-blue-500/30 text-blue-500', color: 'text-blue-500', label: 'PH', title: 'Public Holiday' },
//   weekend: { bg: 'bg-muted border-border text-muted-foreground', color: 'text-muted-foreground', label: 'W', title: 'Week Off' },
// };

// function haversineMetres(lat1: number, lon1: number, lat2: number, lon2: number) {
//   const R = 6371000;
//   const toRad = (d: number) => (d * Math.PI) / 180;
//   const dLat = toRad(lat2 - lat1);
//   const dLon = toRad(lon2 - lon1);
//   const a =
//     Math.sin(dLat / 2) ** 2 +
//     Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
//   return 2 * R * Math.asin(Math.sqrt(a));
// }

// function formatTime(val: string | null | undefined) {
//   if (!val) return null;
//   const match = val.match(/T?(\d{2}):(\d{2})/);
//   if (match) return `${match[1]}:${match[2]}`;
//   const d = new Date(val);
//   if (!Number.isNaN(d.getTime())) {
//     return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: false });
//   }
//   return String(val).slice(0, 5);
// }

// function parseCoordinate(value: number | string | null | undefined) {
//   if (value === null || value === undefined || value === '') return null;
//   const parsed = typeof value === 'number' ? value : Number(value);
//   return Number.isFinite(parsed) ? parsed : null;
// }

// function formatLocation(latitude: number | string | null | undefined, longitude: number | string | null | undefined) {
//   const lat = parseCoordinate(latitude);
//   const lon = parseCoordinate(longitude);
//   if (lat === null || lon === null) return null;
//   return `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
// }

// function formatShiftLabel(shiftType?: string | null) {
//   if (shiftType === 'night') return 'Night shift';
//   if (shiftType === 'day') return 'Day shift';
//   return 'Regular Shift';
// }

// function normalizeAttendanceRecord<T extends AttendanceRecord | null | undefined>(record: T): T {
//   if (!record) return record;
//   return {
//     ...record,
//     checkin_latitude: parseCoordinate(record.checkin_latitude),
//     checkin_longitude: parseCoordinate(record.checkin_longitude),
//     checkout_latitude: parseCoordinate(record.checkout_latitude),
//     checkout_longitude: parseCoordinate(record.checkout_longitude),
//   } as T;
// }

// function normalizeOfficeLocation(value: OfficeLocation | null | undefined): OfficeLocation | null {
//   if (!value || value.configured === false) return null;
//   const latitude = parseCoordinate(value.latitude);
//   const longitude = parseCoordinate(value.longitude);
//   if (latitude === null || longitude === null) return null;
//   return {
//     ...value,
//     name: value.name || 'Head Office',
//     latitude,
//     longitude,
//     radius_meters: Number(value.radius_meters) || 300,
//   };
// }

// export function AttendancePage() {
//   const { hasAnyPermission } = usePermissions();

//   const canManage = hasAnyPermission(['ATTENDANCE_VIEW_ATTENDANCE', 'ATTENDANCE_VIEW_ATTENDANCE', 'ATTENDANCE_VIEW_ATTENDANCE']);
//   const canApprove = hasAnyPermission(['ATTENDANCE_VIEW_ATTENDANCE', 'ATTENDANCE_VIEW_ATTENDANCE', 'ATTENDANCE_VIEW_ATTENDANCE']);

//   const [viewMode, setViewMode] = useState<'my' | 'team'>('my');
//   const [tab, setTab] = useState<'today' | 'monthly' | 'requests' | 'approvals'>('today');

//   // Core data states
//   // eslint-disable-next-line @typescript-eslint/no-explicit-any
//   const [todayData, setTodayData] = useState<any | null>(null);
//   const [office, setOffice] = useState<OfficeLocation | null>(null);
//   const [myAttendance, setMyAttendance] = useState<AttendanceRecord[]>([]);
//   const [holidays, setHolidays] = useState<Holiday[]>([]);
//   const [attendancePolicy, setAttendancePolicy] = useState<AttendancePolicy | null>(null);
//   const [myRequests, setMyRequests] = useState<RegularizationRequest[]>([]);
//   const [approvalsQueue, setApprovalsQueue] = useState<RegularizationRequest[]>([]);

//   // Sub-states & loaders
//   const [loading, setLoading] = useState(false);
//   const [submitting, setSubmitting] = useState(false);
//   const [actioningId, setActioningId] = useState<string | null>(null);
//   const [approvalNote, setApprovalNote] = useState('');
//   const [approvalsFilter, setApprovalsFilter] = useState<'pending' | 'approved' | 'rejected'>('pending');

//   // Month-Year navigation for monthly log
//   const now = new Date();
//   const [month, setMonth] = useState(now.getMonth() + 1);
//   const [year, setYear] = useState(now.getFullYear());

//   // GPS geolocation state
//   const [gps, setGps] = useState<{ latitude: number; longitude: number; accuracy: number } | null>(null);
//   const [locLoading, setLocLoading] = useState(false);
//   const [locError, setLocError] = useState<string | null>(null);
//   const [isWfh, setIsWfh] = useState(false);

//   // Forms
//   const [officeForm, setOfficeForm] = useState({ name: '', latitude: '', longitude: '', radius_meters: '300' });
//   const currentAttendance = todayData?.record || null;
//   const currentEmployeeLabel = currentAttendance?.employee_name || 'Current User';
//   const currentEmployeeCode = currentAttendance?.emp_code || null;
//   const currentShiftLabel = formatShiftLabel(currentAttendance?.shift_type);
//   const [regularizeForm, setRegularizeForm] = useState({ date: '', check_in: '', check_out: '', reason: '' });
//   const [showRegModal, setShowRegModal] = useState(false);

//   const fetchGps = useCallback(() => {
//     if (!navigator.geolocation) {
//       setLocError('Geolocation is not supported by your browser.');
//       return;
//     }
//     setLocLoading(true);
//     setLocError(null);
//     navigator.geolocation.getCurrentPosition(
//       (pos) => {
//         setGps({
//           latitude: pos.coords.latitude,
//           longitude: pos.coords.longitude,
//           accuracy: pos.coords.accuracy,
//         });
//         setLocLoading(false);
//       },
//       (err) => {
//         const messages: Record<number, string> = {
//           1: 'Location permission denied. Please allow location access and try again.',
//           2: 'Location unavailable. Check your GPS/network.',
//           3: 'Location request timed out. Try again.',
//         };
//         setLocError(messages[err.code] || 'Failed to get location.');
//         setGps(null);
//         setLocLoading(false);
//       },
//       { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
//     );
//   }, []);

//   const getFreshGps = useCallback((): Promise<{ latitude: number; longitude: number; accuracy: number } | null> => {
//     if (isWfh || !office) return Promise.resolve(gps);
//     if (!navigator.geolocation) {
//       const message = 'Geolocation is not supported by your browser.';
//       setLocError(message);
//       toast.error(message);
//       return Promise.resolve(null);
//     }

//     setLocLoading(true);
//     setLocError(null);
//     return new Promise((resolve) => {
//       navigator.geolocation.getCurrentPosition(
//         (pos) => {
//           const nextGps = {
//             latitude: pos.coords.latitude,
//             longitude: pos.coords.longitude,
//             accuracy: pos.coords.accuracy,
//           };
//           setGps(nextGps);
//           setLocLoading(false);
//           resolve(nextGps);
//         },
//         (err) => {
//           const messages: Record<number, string> = {
//             1: 'Location permission denied. Please allow location access and try again.',
//             2: 'Location unavailable. Check your GPS/network.',
//             3: 'Location request timed out. Try again.',
//           };
//           const message = messages[err.code] || 'Failed to get location.';
//           setLocError(message);
//           setGps(null);
//           setLocLoading(false);
//           toast.error(message);
//           resolve(null);
//         },
//         { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
//       );
//     });
//   }, [gps, isWfh, office]);

//   const loadData = async (silent = false) => {
//     if (!silent) setLoading(true);
//     try {
//       // 1. Today status
//       const todayRes = await attendanceService.getToday();
//       setTodayData({
//         ...todayRes.data,
//         record: normalizeAttendanceRecord(todayRes.data?.record),
//       });
//       setIsWfh(todayRes.data?.work_mode === 'work_from_home');

//       // 2. Office location
//       try {
//         const officeRes = await attendanceService.getOfficeLocation();
//         const normalizedOffice = normalizeOfficeLocation(officeRes.data);
//         setOffice(normalizedOffice);
//         if (normalizedOffice) {
//           setOfficeForm({
//             name: normalizedOffice.name,
//             latitude: String(normalizedOffice.latitude),
//             longitude: String(normalizedOffice.longitude),
//             radius_meters: String(normalizedOffice.radius_meters),
//           });
//         }
//       } catch {
//         setOffice(null);
//       }

//       // 3. Holidays
//       const holidaysRes = await attendanceService.getHolidays();
//       setHolidays(holidaysRes.data || []);

//       // 4. Requests (regularization)
//       const myReqRes = await attendanceService.getMyRegularizations();
//       setMyRequests(myReqRes.data || []);

//       // 5. Monthly records
//       const myAttRes = await attendanceService.getMyAttendance(month, year);
//       const myAttendancePayload = myAttRes.data as AttendanceRecord[] | { records?: AttendanceRecord[]; policy?: AttendancePolicy };
//       const records = Array.isArray(myAttendancePayload) ? myAttendancePayload : myAttendancePayload?.records || [];
//       setMyAttendance(records.map((record) => normalizeAttendanceRecord(record)));
//       setAttendancePolicy(Array.isArray(myAttendancePayload) ? null : myAttendancePayload?.policy || null);

//       // 6. Approvals (for managers)
//       if (canApprove) {
//         const appRes = await attendanceService.getAllRegularizations(approvalsFilter);
//         setApprovalsQueue(appRes.data || []);
//       }
//     } catch {
//       toast.error('Could not load attendance data');
//     } finally {
//       setLoading(false);
//     }
//   };

//   const gpsDistance = useMemo(() => {
//     if (!gps || !office) return null;
//     return haversineMetres(gps.latitude, gps.longitude, Number(office.latitude), Number(office.longitude));
//   }, [gps, office]);

//   const withinRadius = useMemo(() => {
//     if (isWfh) return true;
//     if (!office) return true;
//     if (gpsDistance === null) return false;
//     return gpsDistance <= office.radius_meters;
//   }, [gpsDistance, office, isWfh]);

//   const handleCheckIn = async () => {
//     try {
//       setSubmitting(true);
//       const currentGps = await getFreshGps();
//       if (!isWfh && office) {
//         if (!currentGps) return;
//         const distance = haversineMetres(currentGps.latitude, currentGps.longitude, Number(office.latitude), Number(office.longitude));
//         if (distance > office.radius_meters) {
//           toast.error('Cannot check-in: You are outside the allowed office perimeter.');
//           return;
//         }
//       }
//       await attendanceService.checkIn(isWfh, currentGps?.latitude ?? null, currentGps?.longitude ?? null);
//       toast.success('Successfully checked in!');
//       await loadData(true);
//     } catch (err) {
//       const errorMsg = (err as { response?: { data?: { error?: string } } }).response?.data?.error || 'Check-in failed';
//       toast.error(errorMsg);
//     } finally {
//       setSubmitting(false);
//     }
//   };

//   const handleCheckOut = async () => {
//     try {
//       setSubmitting(true);
//       if (!todayData?.record?.check_in || todayData?.record?.check_out) {
//         toast.error('No open check-in found. Please check in first or refresh the page.');
//         return;
//       }
//       const currentGps = await getFreshGps();
//       if (!isWfh && office) {
//         if (!currentGps) return;
//         const distance = haversineMetres(currentGps.latitude, currentGps.longitude, Number(office.latitude), Number(office.longitude));
//         if (distance > office.radius_meters) {
//           toast.error('Cannot check-out: You are outside the allowed office perimeter.');
//           return;
//         }
//       }
//       const res = await attendanceService.checkOut(currentGps?.latitude ?? null, currentGps?.longitude ?? null);
//       toast.success(`Checked out! Total hours: ${res.data.hours_worked || 0}h`);
//       await loadData(true);
//     } catch (err) {
//       const errorMsg = (err as { response?: { data?: { error?: string } } }).response?.data?.error || 'Check-out failed';
//       toast.error(errorMsg);
//     } finally {
//       setSubmitting(false);
//     }
//   };

//   const handleSaveOffice = async (e: React.FormEvent) => {
//     e.preventDefault();
//     if (!officeForm.name.trim() || !officeForm.latitude || !officeForm.longitude) {
//       toast.error('Office name, latitude, and longitude are required');
//       return;
//     }
//     try {
//       setSubmitting(true);
//       const payload: OfficeLocation = {
//         name: officeForm.name,
//         latitude: parseFloat(officeForm.latitude),
//         longitude: parseFloat(officeForm.longitude),
//         radius_meters: parseInt(officeForm.radius_meters) || 300,
//       };
//       await attendanceService.setOfficeLocation(payload);
//       toast.success('Office coordinates updated successfully');
//       await loadData(true);
//     } catch {
//       toast.error('Could not update office location');
//     } finally {
//       setSubmitting(false);
//     }
//   };

//   const handleRaiseRegularization = async (e: React.FormEvent) => {
//     e.preventDefault();
//     if (!regularizeForm.date || !regularizeForm.reason.trim()) {
//       toast.error('Date and reason are required');
//       return;
//     }
//     try {
//       setSubmitting(true);
//       const payload = {
//         date: regularizeForm.date,
//         requested_check_in: regularizeForm.check_in || undefined,
//         requested_check_out: regularizeForm.check_out || undefined,
//         reason: regularizeForm.reason,
//       };
//       await attendanceService.applyRegularization(payload);
//       toast.success('Regularization request submitted!');
//       setRegularizeForm({ date: '', check_in: '', check_out: '', reason: '' });
//       setShowRegModal(false);
//       await loadData(true);
//     } catch (err: any) {
//       const data = err.response?.data;
//       let errorMsg = 'Failed to submit regularization request';
//       if (data) {
//         if (typeof data.error === 'string') {
//           errorMsg = data.error;
//         } else if (typeof data === 'object') {
//           // Flatten DRF error object: e.g. { log_date: ["This field is required."] }
//           const errors = Object.values(data).flat();
//           if (errors.length > 0 && typeof errors[0] === 'string') {
//             errorMsg = errors.join(' | ');
//           }
//         }
//       }
//       toast.error(errorMsg);
//     } finally {
//       setSubmitting(false);
//     }
//   };

//   const handleApprovalAction = async (id: string, action: 'approve' | 'reject') => {
//     try {
//       setActioningId(id);
//       await attendanceService.actionRegularization(id, action, approvalNote);
//       toast.success(`Request successfully ${action}d`);
//       setApprovalNote('');
//       await loadData(true);
//     } catch {
//       toast.error('Approval operation failed');
//     } finally {
//       setActioningId(null);
//     }
//   };

//   // Monthly Calendar construction helpers
//   const daysInMonth = useMemo(() => new Date(year, month, 0).getDate(), [month, year]);
//   const firstDayIndex = useMemo(() => new Date(year, month - 1, 1).getDay(), [month, year]);
//   const calendarCells = useMemo(() => {
//     const cells = [];
//     for (let i = 0; i < firstDayIndex; i++) cells.push(null);
//     for (let d = 1; d <= daysInMonth; d++) cells.push(d);
//     return cells;
//   }, [firstDayIndex, daysInMonth]);

//   const monthName = useMemo(() => {
//     return new Date(year, month - 1).toLocaleString('en-US', { month: 'long', year: 'numeric' });
//   }, [month, year]);

//   const officeMapUrl = useMemo(() => {
//     if (!office) return '';
//     const lat = Number(office.latitude);
//     const lon = Number(office.longitude);
//     if (!Number.isFinite(lat) || !Number.isFinite(lon)) return '';
//     const spread = 0.004;
//     const bbox = [lon - spread, lat - spread, lon + spread, lat + spread].join('%2C');
//     return `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat}%2C${lon}`;
//   }, [office]);
//   const checkinLocation = formatLocation(todayData?.record?.checkin_latitude, todayData?.record?.checkin_longitude);
//   const checkoutLocation = formatLocation(todayData?.record?.checkout_latitude, todayData?.record?.checkout_longitude);

//   const attendanceLookup = useMemo(() => {
//     const map: Record<string, AttendanceRecord> = {};
//     myAttendance.forEach((rec) => {
//       map[rec.date] = rec;
//     });
//     return map;
//   }, [myAttendance]);

//   const myRequestsLookup = useMemo(() => {
//     const map: Record<string, RegularizationRequest> = {};
//     myRequests.forEach((req) => {
//       if (req.status === 'pending') {
//         map[req.date] = req;
//       }
//     });
//     return map;
//   }, [myRequests]);

//   const weekendDays = useMemo(
//     () => new Set((attendancePolicy?.weekend_days || ['saturday', 'sunday']).map((day) => day.toLowerCase())),
//     [attendancePolicy]
//   );

//   const isWeekendDate = useCallback(
//     (value: Date) => {
//       const names = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
//       return weekendDays.has(names[value.getDay()]);
//     },
//     [weekendDays]
//   );

//   const holidayLookup = useMemo(() => {
//     const map: Record<string, string> = {};
//     holidays.forEach((h) => {
//       map[h.date] = h.name;
//     });
//     return map;
//   }, [holidays]);

//   const handlePrevMonth = () => {
//     if (month === 1) {
//       setMonth(12);
//       setYear((y) => y - 1);
//     } else {
//       setMonth((m) => m - 1);
//     }
//   };

//   const handleNextMonth = () => {
//     if (month === 12) {
//       setMonth(1);
//       setYear((y) => y + 1);
//     } else {
//       setMonth((m) => m + 1);
//     }
//   };

//   useEffect(() => {
//     loadData();
//   }, [month, year, approvalsFilter]);

//   const [portalNode, setPortalNode] = useState<HTMLElement | null>(null);
//   useEffect(() => {
//     setPortalNode(document.getElementById('hrms-header-portal'));
//   }, []);

//   const headerContent = (
//     <PageHeader
//       title="Attendance & Check-in"
//       description="Verify your position, check in/out, view timesheets, and apply for corrections."
//       actions={
//         <Button size="sm" onClick={() => loadData()} disabled={loading} className="flex items-center gap-1.5">
//           <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
//           Refresh Data
//         </Button>
//       }
//     />
//   );

//   return (
//     <div className="space-y-6">
//       {portalNode ? createPortal(headerContent, portalNode) : headerContent}

//       {/* View Mode Toggles (Missing Feature Restored) */}
//       {canManage && (
//         <div className="flex p-1 bg-muted rounded-full w-fit mb-2">
//           <button
//             onClick={() => setViewMode('my')}
//             className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${viewMode === 'my' ? 'bg-background shadow text-foreground border border-border' : 'text-muted-foreground hover:bg-muted/50 border border-transparent'
//               }`}
//           >
//             My attendance
//           </button>
//           <button
//             onClick={() => setViewMode('team')}
//             className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${viewMode === 'team' ? 'bg-background shadow text-foreground border border-border' : 'text-muted-foreground hover:bg-muted/50 border border-transparent'
//               }`}
//           >
//             Attendance
//           </button>
//         </div>
//       )}

//       {viewMode === 'team' ? (
//         <Card className="mt-6">
//           <CardHeader>
//             <CardTitle className="text-base">Team Attendance Records</CardTitle>
//           </CardHeader>
//           <CardContent>
//             <div className="py-16 text-center text-muted-foreground flex flex-col items-center gap-2 border border-dashed rounded-xl">
//               <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
//                 <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
//                 <circle cx="9" cy="7" r="4"></circle>
//                 <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
//                 <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
//               </svg>
//               <p className="font-semibold text-sm mt-2">Team Attendance Interface</p>
//               <p className="text-xs max-w-sm">This module allows you to review and override team member attendance records. Team data will populate here based on selected filters.</p>
//             </div>
//           </CardContent>
//         </Card>
//       ) : (
//         <>
//           <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
//             <span className="rounded-full border bg-muted/40 px-3 py-1 font-semibold text-foreground">{currentEmployeeLabel}</span>
//             {currentEmployeeCode && <span className="rounded-full border bg-muted/20 px-3 py-1 font-mono">{currentEmployeeCode}</span>}
//             <span className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1 font-semibold text-primary">
//               {currentShiftLabel}
//             </span>
//           </div>

//           {/* Tabs */}
//           <div className="flex p-1 bg-muted rounded-xl w-fit border border-border">
//             <button
//               onClick={() => setTab('today')}
//               className={cn(
//                 'px-4 py-2 rounded-lg text-xs font-semibold transition-all active:scale-95',
//                 tab === 'today' ? 'bg-card text-foreground shadow-sm border border-border' : 'text-muted-foreground hover:text-foreground'
//               )}
//             >
//               📍 Today
//             </button>
//             <button
//               onClick={() => setTab('monthly')}
//               className={cn(
//                 'px-4 py-2 rounded-lg text-xs font-semibold transition-all active:scale-95',
//                 tab === 'monthly' ? 'bg-card text-foreground shadow-sm border border-border' : 'text-muted-foreground hover:text-foreground'
//               )}
//             >
//               📅 Monthly Records
//             </button>
//             <button
//               onClick={() => setTab('requests')}
//               className={cn(
//                 'px-4 py-2 rounded-lg text-xs font-semibold transition-all active:scale-95',
//                 tab === 'requests' ? 'bg-card text-foreground shadow-sm border border-border' : 'text-muted-foreground hover:text-foreground'
//               )}
//             >
//               📝 My Requests
//             </button>
//             {canApprove && (
//               <button
//                 onClick={() => setTab('approvals')}
//                 className={cn(
//                   'px-4 py-2 rounded-lg text-xs font-semibold transition-all active:scale-95',
//                   tab === 'approvals' ? 'bg-card text-foreground shadow-sm border border-border' : 'text-muted-foreground hover:text-foreground'
//                 )}
//               >
//                 ✅ Approvals Queue
//               </button>
//             )}
//           </div>

//           {loading && !todayData ? (
//             <div className="flex justify-center py-20">
//               <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
//             </div>
//           ) : (
//             <>
//               {/* TAB 1: TODAY CHECK-IN / CHECK-OUT */}
//               {tab === 'today' && (
//                 <div className="grid gap-6 lg:grid-cols-3">
//                   <div className="lg:col-span-2 space-y-6">
//                     <Card>
//                       <CardContent className="space-y-6">
//                         {/* Geolocation Coordinate Inspector Card */}
//                         {false && !isWfh && office && (
//                           <Card className="bg-muted/20 border-dashed">
//                             <CardContent className="p-4 space-y-3">
//                               <div className="flex items-center justify-between text-xs">
//                                 <span className="font-semibold text-muted-foreground">Geofencing perimeter validation</span>
//                                 {locLoading ? (
//                                   <span className="flex items-center gap-1 text-primary">
//                                     <Loader2 className="h-3.5 w-3.5 animate-spin" /> Fetching location...
//                                   </span>
//                                 ) : gps ? (
//                                   <Badge variant={withinRadius ? 'success' : 'destructive'} className="text-[10px]">
//                                     {withinRadius ? 'Within Range' : 'Out of Bounds'}
//                                   </Badge>
//                                 ) : (
//                                   <span className="text-destructive font-semibold">Location Unknown</span>
//                                 )}
//                               </div>

//                               <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
//                                 <div className="p-2.5 bg-background border rounded-lg space-y-1">
//                                   <p className="text-[10px] font-bold text-muted-foreground uppercase">Target Office Location</p>
//                                   <p className="font-mono text-[11px] text-foreground font-semibold">{office!.name}</p>
//                                   <p className="font-mono text-[10px] text-muted-foreground">
//                                     Coordinates: {Number(office!.latitude).toFixed(6)}, {Number(office!.longitude).toFixed(6)}
//                                   </p>
//                                   <p className="font-mono text-[10px] text-muted-foreground">Geofence Radius: {office!.radius_meters}m</p>
//                                 </div>

//                                 <div className="p-2.5 bg-background border rounded-lg space-y-1">
//                                   <p className="text-[10px] font-bold text-muted-foreground uppercase">Your Current GPS Position</p>
//                                   {gps ? (
//                                     <>
//                                       <p className="font-mono text-[11px] text-foreground font-semibold">
//                                         {gps!.latitude.toFixed(6)}, {gps!.longitude.toFixed(6)}
//                                       </p>
//                                       <p className="font-mono text-[10px] text-muted-foreground">Accuracy: ±{Math.round(gps!.accuracy)}m</p>
//                                       {gpsDistance !== null && (
//                                         <p className="font-mono text-[10px] text-primary font-semibold">
//                                           Distance: {Math.round(gpsDistance!)}m from center
//                                         </p>
//                                       )}
//                                     </>
//                                   ) : (
//                                     <p className="text-muted-foreground italic text-[11px]">No GPS coordinate lock acquired.</p>
//                                   )}
//                                 </div>
//                               </div>

//                               {locError && (
//                                 <div className="flex gap-1.5 text-xs text-yellow-500 bg-yellow-500/5 p-2.5 rounded-lg border border-yellow-500/20">
//                                   <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
//                                   <div>
//                                     <p className="font-semibold">GPS Error Lock Alert</p>
//                                     <p className="text-[10px] text-yellow-500/80">{locError}</p>
//                                   </div>
//                                 </div>
//                               )}

//                               <Button
//                                 size="sm"
//                                 variant="outline"
//                                 onClick={fetchGps}
//                                 disabled={locLoading}
//                                 className="w-full text-xs flex items-center justify-center gap-1.5"
//                               >
//                                 <MapPin className="h-3.5 w-3.5" />
//                                 Force GPS Coordinate Refresh
//                               </Button>
//                             </CardContent>
//                           </Card>
//                         )}

//                         {/* Clock buttons */}
//                         <div className="grid grid-cols-2 gap-4">
//                           <div className="p-4 border rounded-xl bg-muted/10 space-y-2 text-xs">
//                             <p className="font-semibold text-muted-foreground flex items-center gap-1">
//                               <Clock className="h-3.5 w-3.5 text-emerald-500" />
//                               Check-In Time
//                             </p>
//                             <p className="text-xl font-bold text-foreground">
//                               {todayData?.record?.check_in ? formatTime(todayData.record.check_in) : '--:--'}
//                             </p>
//                             <p className="text-[10px] text-muted-foreground">
//                               {checkinLocation
//                                 ? `Location logged: ${checkinLocation}`
//                                 : isWfh
//                                   ? 'Logged as Remote check-in'
//                                   : 'No clock-in captured yet.'}
//                             </p>
//                           </div>

//                           <div className="p-4 border rounded-xl bg-muted/10 space-y-2 text-xs">
//                             <p className="font-semibold text-muted-foreground flex items-center gap-1">
//                               <Clock className="h-3.5 w-3.5 text-rose-500" />
//                               Check-Out Time
//                             </p>
//                             <p className="text-xl font-bold text-foreground">
//                               {todayData?.record?.check_out ? formatTime(todayData.record.check_out) : '--:--'}
//                             </p>
//                             <p className="text-[10px] text-muted-foreground">
//                               {checkoutLocation
//                                 ? `Location logged: ${checkoutLocation}`
//                                 : 'No clock-out captured yet.'}
//                             </p>
//                           </div>
//                         </div>

//                         {/* Checkin / Checkout buttons triggers */}
//                         {!todayData?.record?.check_in ? (
//                           <Button
//                             onClick={handleCheckIn}
//                             disabled={submitting || (!isWfh && !!office && locLoading)}
//                             className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold h-12 flex items-center justify-center gap-1.5"
//                           >
//                             {submitting && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
//                             Check-in (Punch Work Start)
//                           </Button>
//                         ) : !todayData?.record?.check_out ? (
//                           <Button
//                             onClick={handleCheckOut}
//                             disabled={submitting || (!isWfh && !!office && locLoading)}
//                             className="w-full bg-rose-600 hover:bg-rose-700 text-white font-bold h-12 flex items-center justify-center gap-1.5"
//                           >
//                             {submitting && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
//                             Check-out (Punch Work Finish)
//                           </Button>
//                         ) : (
//                           <div className="text-center p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 rounded-xl space-y-1">
//                             <CheckCircle2 className="h-6 w-6 mx-auto mb-1 text-emerald-500" />
//                             <p className="text-xs font-semibold">Today's Clock punches are complete!</p>
//                             <p className="text-[10px] text-emerald-500/70">
//                               Total Hours: {todayData.record.hours_worked}h | Overtime: {todayData.record.ot_hours}h
//                             </p>
//                           </div>
//                         )}

//                         <div className="text-center">
//                           <button
//                             onClick={() => {
//                               setRegularizeForm({
//                                 date: todayData?.record?.date || new Date().toISOString().split('T')[0],
//                                 check_in: todayData?.record?.check_in ? formatTime(todayData.record.check_in) || '' : '',
//                                 check_out: todayData?.record?.check_out ? formatTime(todayData.record.check_out) || '' : '',
//                                 reason: '',
//                               });
//                               setShowRegModal(true);
//                             }}
//                             className="text-xs text-primary underline hover:text-primary/80"
//                           >
//                             Missed a punch clock register? Apply for Regularization correction
//                           </button>
//                         </div>
//                       </CardContent>
//                     </Card>
//                   </div>

//                   {/* Office Location perimeter configuration */}
//                   <div className="space-y-6">
//                     {false && canManage && (
//                       <Card>
//                         <CardHeader>
//                           <CardTitle className="text-base">Configure Office Center Geofence</CardTitle>
//                         </CardHeader>
//                         <CardContent>
//                           <form onSubmit={handleSaveOffice} className="space-y-4 text-xs">
//                             <div className="space-y-1.5">
//                               <label className="font-semibold text-muted-foreground">Office Center Name</label>
//                               <Input
//                                 value={officeForm.name}
//                                 onChange={(e) => setOfficeForm((p) => ({ ...p, name: e.target.value }))}
//                                 placeholder="e.g. Headquarters Office"
//                                 required
//                               />
//                             </div>

//                             <div className="space-y-1.5">
//                               <label className="font-semibold text-muted-foreground">Center Latitude Coordinates</label>
//                               <Input
//                                 value={officeForm.latitude}
//                                 onChange={(e) => setOfficeForm((p) => ({ ...p, latitude: e.target.value }))}
//                                 placeholder="e.g. 12.971598"
//                                 required
//                               />
//                             </div>

//                             <div className="space-y-1.5">
//                               <label className="font-semibold text-muted-foreground">Center Longitude Coordinates</label>
//                               <Input
//                                 value={officeForm.longitude}
//                                 onChange={(e) => setOfficeForm((p) => ({ ...p, longitude: e.target.value }))}
//                                 placeholder="e.g. 77.594562"
//                                 required
//                               />
//                             </div>

//                             <div className="space-y-1.5">
//                               <label className="font-semibold text-muted-foreground">Perimeter Zone Radius (Meters)</label>
//                               <Input
//                                 type="number"
//                                 value={officeForm.radius_meters}
//                                 onChange={(e) => setOfficeForm((p) => ({ ...p, radius_meters: e.target.value }))}
//                                 placeholder="e.g. 100"
//                                 required
//                               />
//                             </div>

//                             <Button type="submit" disabled={submitting} className="w-full flex items-center justify-center gap-1.5">
//                               {submitting && <Loader2 className="h-3 w-3 animate-spin" />}
//                               Save Geofencing Rules
//                             </Button>
//                           </form>
//                         </CardContent>
//                       </Card>
//                     )}

//                     <Card>
//                       <CardHeader>
//                         <CardTitle className="text-base">System Settings Location Map</CardTitle>
//                       </CardHeader>
//                       <CardContent className="space-y-4 text-xs">
//                         {office && officeMapUrl ? (
//                           <>
//                             <div className="relative h-64 overflow-hidden rounded-xl border bg-muted">
//                               <iframe
//                                 title="Office geofence map"
//                                 src={officeMapUrl}
//                                 className="h-full w-full"
//                                 loading="lazy"
//                               />
//                               <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
//                                 <div className="h-32 w-32 rounded-full border-2 border-primary bg-primary/10 shadow-[0_0_0_999px_rgba(255,255,255,0.02)]" />
//                               </div>
//                               <div className="absolute left-3 top-3 rounded-lg border bg-background/95 px-3 py-2 shadow-sm">
//                                 <p className="font-semibold text-foreground">{office.name || 'Head Office'}</p>
//                                 <p className="text-[10px] text-muted-foreground">
//                                   Allowed radius: {office.radius_meters || 300} meters
//                                 </p>
//                               </div>
//                             </div>

//                             <div className="grid gap-3">
//                               <div className="flex items-center justify-between border-b pb-2">
//                                 <span className="text-muted-foreground font-medium">System Setting Coordinates</span>
//                                 <span className="font-mono text-[10px] font-bold text-foreground">
//                                   {Number(office.latitude).toFixed(6)}, {Number(office.longitude).toFixed(6)}
//                                 </span>
//                               </div>
//                               <div className="flex items-center justify-between border-b pb-2">
//                                 <span className="text-muted-foreground font-medium">Your Distance</span>
//                                 <span className={cn('font-bold', withinRadius ? 'text-emerald-600' : 'text-rose-600')}>
//                                   {gpsDistance === null ? 'Waiting for GPS' : `${Math.round(gpsDistance)} meters`}
//                                 </span>
//                               </div>
//                               <div className="flex items-center justify-between">
//                                 <span className="text-muted-foreground font-medium">Check-in Permission</span>
//                                 <Badge variant={withinRadius ? 'success' : 'destructive'}>
//                                   {withinRadius ? 'Allowed' : 'Blocked'}
//                                 </Badge>
//                               </div>
//                             </div>
//                           </>
//                         ) : (
//                           <div className="rounded-xl border border-dashed p-6 text-center text-muted-foreground">
//                             Office latitude and longitude are not configured in system settings.
//                           </div>
//                         )}
//                       </CardContent>
//                     </Card>
//                   </div>
//                 </div>
//               )}

//               {/* TAB 2: MONTHLY VIEW CALENDAR GRID */}
//               {tab === 'monthly' && (
//                 <Card>
//                   <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-4">
//                     <CardTitle className="text-base">Attendance Calendar Sheet</CardTitle>

//                     {/* Calendar month selector controls */}
//                     <div className="flex items-center gap-3">
//                       <Button size="icon" variant="outline" onClick={handlePrevMonth} className="h-8 w-8">
//                         &lt;
//                       </Button>
//                       <span className="font-bold text-xs w-28 text-center">{monthName}</span>
//                       <Button size="icon" variant="outline" onClick={handleNextMonth} className="h-8 w-8">
//                         &gt;
//                       </Button>
//                     </div>
//                   </CardHeader>
//                   <CardContent className="space-y-6">
//                     {/* Legend colors */}
//                     <div className="flex flex-wrap items-center gap-2 text-[10px] text-muted-foreground border-b pb-3 border-border">
//                       {Object.entries(STATUS_COLOR).map(([key, val]) => (
//                         <div key={key} className="flex items-center gap-1 border px-2 py-1 rounded bg-muted/10">
//                           <span className={cn('h-2.5 w-2.5 rounded-sm', key === 'weekend' ? 'bg-muted border border-border' : 'bg-current', val.color)} />
//                           <span className="font-medium">{val.title}</span>
//                         </div>
//                       ))}
//                       <div className="flex items-center gap-1 border px-2 py-1 rounded bg-muted/10">
//                         <span className="h-2.5 w-2.5 rounded-sm bg-purple-500/10 border border-purple-500/30" />
//                         <span className="font-medium text-purple-500">Overtime (OT)</span>
//                       </div>
//                     </div>
//                     {attendancePolicy && (
//                       <div className="grid gap-2 rounded-lg border bg-muted/10 p-3 text-[10px] text-muted-foreground sm:grid-cols-5">
//                         <span>Shift: <b className="text-foreground">{attendancePolicy.shift_start} - {attendancePolicy.shift_end}</b></span>
//                         {attendancePolicy.night_shift_enabled && (
//                           <span>Night: <b className="text-foreground">{attendancePolicy.night_shift_start} - {attendancePolicy.night_shift_end}</b></span>
//                         )}
//                         <span>Grace: <b className="text-foreground">{attendancePolicy.grace_minutes} min</b></span>
//                         <span>Half day below: <b className="text-foreground">{attendancePolicy.half_day_hours}h</b></span>
//                         <span>Weekends: <b className="text-foreground">{attendancePolicy.weekend_days?.join(', ') || 'none'}</b></span>
//                       </div>
//                     )}

//                     {/* Calendar Grid */}
//                     <div className="border rounded-xl overflow-hidden bg-card text-xs">
//                       {/* Headers */}
//                       <div className="grid grid-cols-7 border-b bg-muted/40 font-semibold text-center text-muted-foreground">
//                         {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d, index) => {
//                           const names = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
//                           const isWeekendDay = weekendDays.has(names[index]);
//                           return (
//                             <div key={d} className={cn('py-2 border-r last:border-r-0', isWeekendDay && 'bg-muted/70')}>
//                               {d}
//                             </div>
//                           );
//                         })}
//                       </div>

//                       {/* Cell days */}
//                       <div className="grid grid-cols-7 grid-flow-row">
//                         {calendarCells.map((day, cellIndex) => {
//                           if (!day) return <div key={`empty-${cellIndex}`} className="min-h-[70px] border-r border-b bg-muted/20" />;

//                           const dateString = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
//                           const record = attendanceLookup[dateString];
//                           const holidayName = holidayLookup[dateString] || record?.holiday_name;

//                           const cellDate = new Date(dateString);
//                           const isWeekendDay = isWeekendDate(cellDate);
//                           const cellToday = dateString === new Date().toISOString().split('T')[0];

//                           let statusKey = record?.status;
//                           if (record && !record.check_out && !['leave', 'lop_leave', 'holiday'].includes(record.status) && dateString !== new Date().toISOString().split('T')[0]) {
//                             statusKey = 'missing';
//                           }
//                           if (record?.pending_reason === 'missing_attendance' || record?.pending_reason === 'missing_checkout') {
//                             statusKey = 'missing';
//                           }

//                           const pendingReq = myRequestsLookup[dateString];
//                           if (pendingReq) {
//                             statusKey = 'pending';
//                           }

//                           let displayColor = STATUS_COLOR.weekend;
//                           if (record) {
//                             displayColor = STATUS_COLOR[statusKey || ''] || STATUS_COLOR.absent;
//                           } else if (holidayName) {
//                             displayColor = STATUS_COLOR.holiday;
//                           }

//                           const hasOT = record && record.check_in && record.check_out && record.ot_hours > 0;
//                           const checkInFormatted = record?.check_in ? formatTime(record.check_in) : null;
//                           const checkOutFormatted = record?.check_out ? formatTime(record.check_out) : null;

//                           return (
//                             <div
//                               key={day}
//                               onClick={() => {
//                                 if (isWeekendDay || holidayName) return;
//                                 setRegularizeForm({
//                                   date: dateString,
//                                   check_in: checkInFormatted || '',
//                                   check_out: checkOutFormatted || '',
//                                   reason: '',
//                                 });
//                                 setShowRegModal(true);
//                               }}
//                               className={cn(
//                                 'min-h-[75px] border-r border-b p-1.5 flex flex-col justify-between hover:bg-muted/30 cursor-pointer transition-colors',
//                                 cellToday && 'bg-primary/5 ring-1 ring-primary/30 ring-inset'
//                               )}
//                             >
//                               {/* Date and tags */}
//                               <div className="flex items-center justify-between">
//                                 <span className={cn('font-bold', cellToday && 'text-primary')}>{day}</span>
//                                 <div className="flex gap-0.5">
//                                   {holidayName && <Badge className="text-[8px] bg-blue-500/10 border-blue-500/30 text-blue-500 py-0 px-1">PH</Badge>}
//                                   {record && <Badge className={cn('text-[8px] py-0 px-1', displayColor.bg)}>{displayColor.label}</Badge>}
//                                 </div>
//                               </div>

//                               {/* Detail information inside cell */}
//                               <div className="mt-1 space-y-0.5">
//                                 <div className="flex flex-wrap items-center gap-1">
//                                   <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-1.5 py-0.5 text-[8px] font-semibold uppercase text-emerald-600">
//                                     In
//                                   </span>
//                                   <p className="text-[9px] text-foreground font-medium">{checkInFormatted || '--:--'}</p>
//                                 </div>
//                                 <div className="flex flex-wrap items-center gap-1">
//                                   <span className="rounded-full border border-rose-500/20 bg-rose-500/10 px-1.5 py-0.5 text-[8px] font-semibold uppercase text-rose-600">
//                                     Out
//                                   </span>
//                                   <p className="text-[9px] text-foreground font-medium">{checkOutFormatted || '--:--'}</p>
//                                 </div>
//                                 {hasOT && (
//                                   <p className="text-[8px] text-purple-500 font-bold">
//                                     OT +{record?.ot_hours}h
//                                   </p>
//                                 )}
//                                 {statusKey === 'late' && (
//                                   <p className="text-[8px] text-yellow-500 font-semibold">Late entry</p>
//                                 )}
//                                 {holidayName && (
//                                   <p className="text-[8px] text-blue-500 font-medium truncate max-w-full">{holidayName}</p>
//                                 )}
//                               </div>
//                             </div>
//                           );
//                         })}
//                       </div>
//                     </div>
//                   </CardContent>
//                 </Card>
//               )}

//               {/* TAB 3: MY REQUESTS (REGULARIZATION LIST) */}
//               {tab === 'requests' && (
//                 <Card>
//                   <CardHeader className="flex flex-row items-center justify-between">
//                     <CardTitle className="text-base">Correction Submissions Log</CardTitle>
//                     <Button
//                       size="sm"
//                       onClick={() => {
//                         setRegularizeForm({
//                           date: new Date().toISOString().split('T')[0],
//                           check_in: '',
//                           check_out: '',
//                           reason: '',
//                         });
//                         setShowRegModal(true);
//                       }}
//                       className="flex items-center gap-1.5"
//                     >
//                       Apply Correction
//                     </Button>
//                   </CardHeader>
//                   <CardContent>
//                     {myRequests.length === 0 ? (
//                       <div className="text-center py-12 text-xs text-muted-foreground border-dashed border-2 rounded-xl">
//                         No regularization correction applications filed.
//                       </div>
//                     ) : (
//                       <div className="space-y-3">
//                         {myRequests.map((req) => (
//                           <div key={req.id} className="border p-4 rounded-xl text-xs space-y-2 bg-muted/20">
//                             <div className="flex items-center justify-between">
//                               <span className="font-bold text-foreground text-sm">{req.date}</span>
//                               <Badge
//                                 variant={req.status === 'approved' ? 'success' : req.status === 'rejected' ? 'destructive' : 'warning'}
//                               >
//                                 {req.status}
//                               </Badge>
//                             </div>
//                             <p className="text-muted-foreground">
//                               Requested Corrections: <strong className="text-foreground">{req.requested_check_in || '—'} → {req.requested_check_out || '—'}</strong>
//                             </p>
//                             <p className="text-muted-foreground">
//                               Reason: <span className="text-foreground">{req.reason}</span>
//                             </p>
//                             {req.manager_note && (
//                               <div className="bg-background border rounded-lg p-2 mt-1 text-[11px] text-yellow-500/80">
//                                 <strong>Approver's Feedback:</strong> {req.manager_note}
//                               </div>
//                             )}
//                           </div>
//                         ))}
//                       </div>
//                     )}
//                   </CardContent>
//                 </Card>
//               )}

//               {/* TAB 4: APPROVALS QUEUE (MANAGERS ONLY) */}
//               {tab === 'approvals' && (
//                 <Card>
//                   <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-4">
//                     <CardTitle className="text-base">Regularization Queue Reviews</CardTitle>

//                     {/* Filter button triggers */}
//                     <div className="flex gap-1 bg-muted p-0.5 rounded-lg border text-xs">
//                       {(['pending', 'approved', 'rejected'] as const).map((filterOpt) => (
//                         <button
//                           key={filterOpt}
//                           onClick={() => setApprovalsFilter(filterOpt)}
//                           className={cn(
//                             'px-3 py-1.5 rounded-md font-semibold capitalize transition-all',
//                             approvalsFilter === filterOpt ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
//                           )}
//                         >
//                           {filterOpt}
//                         </button>
//                       ))}
//                     </div>
//                   </CardHeader>
//                   <CardContent>
//                     {approvalsQueue.length === 0 ? (
//                       <div className="text-center py-12 text-xs text-muted-foreground">
//                         No regularization requests in this category.
//                       </div>
//                     ) : (
//                       <div className="space-y-4">
//                         {approvalsQueue.map((req) => (
//                           <div key={req.id} className="border p-4 rounded-xl text-xs space-y-3 bg-muted/20">
//                             <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
//                               <div>
//                                 <span className="font-bold text-foreground text-sm">{req.employee_name}</span>
//                                 <span className="text-muted-foreground mx-2">•</span>
//                                 <span className="text-muted-foreground">Date: {req.date}</span>
//                               </div>
//                               <Badge
//                                 variant={req.status === 'approved' ? 'success' : req.status === 'rejected' ? 'destructive' : 'warning'}
//                               >
//                                 {req.status}
//                               </Badge>
//                             </div>

//                             <div className="space-y-1.5 p-3 bg-background border rounded-lg">
//                               <p className="text-muted-foreground">
//                                 Correction Request: <strong className="text-foreground">{req.requested_check_in || '—'} → {req.requested_check_out || '—'}</strong>
//                               </p>
//                               <p className="text-muted-foreground">
//                                 Employee Justification: <span className="text-foreground">{req.reason}</span>
//                               </p>
//                             </div>

//                             {req.status === 'pending' && (
//                               <div className="space-y-2.5 pt-2 border-t">
//                                 <div className="space-y-1.5">
//                                   <label className="font-semibold text-muted-foreground">Resolution Note / feedback</label>
//                                   <Input
//                                     value={approvalNote}
//                                     onChange={(e) => setApprovalNote(e.target.value)}
//                                     placeholder="Explain approval/rejection details (optional)..."
//                                   />
//                                 </div>
//                                 <div className="flex gap-2 justify-end">
//                                   <Button
//                                     size="sm"
//                                     variant="outline"
//                                     className="bg-red-500/10 hover:bg-red-500/20 text-red-500 border-red-500/20"
//                                     onClick={() => handleApprovalAction(req.id, 'reject')}
//                                     disabled={Boolean(actioningId)}
//                                   >
//                                     {actioningId === req.id && <Loader2 className="h-3 w-3 animate-spin mr-1" />}
//                                     Reject Request
//                                   </Button>
//                                   <Button
//                                     size="sm"
//                                     onClick={() => handleApprovalAction(req.id, 'approve')}
//                                     disabled={Boolean(actioningId)}
//                                   >
//                                     {actioningId === req.id && <Loader2 className="h-3 w-3 animate-spin mr-1" />}
//                                     Approve & Correction
//                                   </Button>
//                                 </div>
//                               </div>
//                             )}
//                           </div>
//                         ))}
//                       </div>
//                     )}
//                   </CardContent>
//                 </Card>
//               )}
//             </>
//           )}

//           {/* REGULARIZATION FORM DIALOG MODAL */}
//           {showRegModal && (
//             <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs">
//               <Card className="w-full max-w-md mx-4">
//                 <CardHeader className="flex flex-row items-center justify-between pb-3 border-b">
//                   <CardTitle className="text-base">Apply Attendance Correction</CardTitle>
//                   <button onClick={() => setShowRegModal(false)} className="text-muted-foreground hover:text-foreground">
//                     <X className="h-4 w-4" />
//                   </button>
//                 </CardHeader>
//                 <CardContent className="pt-4">
//                   <form onSubmit={handleRaiseRegularization} className="space-y-4 text-xs">
//                     <div className="space-y-1.5">
//                       <label className="font-semibold text-muted-foreground">Log Date</label>
//                       <Input
//                         type="date"
//                         value={regularizeForm.date}
//                         onChange={(e) => setRegularizeForm((p) => ({ ...p, date: e.target.value }))}
//                         disabled={submitting}
//                         required
//                       />
//                     </div>

//                     <div className="grid grid-cols-2 gap-3">
//                       <div className="space-y-1.5">
//                         <label className="font-semibold text-muted-foreground">Correction Check-In</label>
//                         <Input
//                           type="time"
//                           value={regularizeForm.check_in}
//                           onChange={(e) => setRegularizeForm((p) => ({ ...p, check_in: e.target.value }))}
//                           disabled={submitting}
//                         />
//                       </div>

//                       <div className="space-y-1.5">
//                         <label className="font-semibold text-muted-foreground">Correction Check-Out</label>
//                         <Input
//                           type="time"
//                           value={regularizeForm.check_out}
//                           onChange={(e) => setRegularizeForm((p) => ({ ...p, check_out: e.target.value }))}
//                           disabled={submitting}
//                         />
//                       </div>
//                     </div>

//                     <div className="space-y-1.5">
//                       <label className="font-semibold text-muted-foreground">Justification Reason *</label>
//                       <textarea
//                         value={regularizeForm.reason}
//                         onChange={(e) => setRegularizeForm((p) => ({ ...p, reason: e.target.value }))}
//                         rows={3}
//                         className="w-full bg-background border border-input text-foreground rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary text-xs"
//                         placeholder="Provide justification why clock register was missing..."
//                         disabled={submitting}
//                         required
//                       />
//                     </div>

//                     <div className="flex gap-2 justify-end pt-3 border-t">
//                       <Button type="button" variant="outline" onClick={() => setShowRegModal(false)} disabled={submitting}>
//                         Cancel
//                       </Button>
//                       <Button type="submit" disabled={submitting}>
//                         {submitting && <Loader2 className="h-4 w-4 animate-spin mr-1.5" />}
//                         Submit Application
//                       </Button>
//                     </div>
//                   </form>
//                 </CardContent>
//               </Card>
//             </div>
//           )}
//         </>
//       )}
//     </div>
//   );
// }

// export default AttendancePage;


/* eslint-disable react-hooks/set-state-in-effect */
/* eslint-disable react-hooks/exhaustive-deps */
import { useEffect, useState, useMemo, useCallback } from 'react';
import { MapPin, Clock, Loader2, CheckCircle2, AlertTriangle, RefreshCw, X, Filter, CalendarDays, Users, Search } from 'lucide-react';
import { PageHeader } from '@/components/shared/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { usePermissions } from '@/auth/usePermissions';
import { attendanceService, AttendanceRecord, AttendancePolicy, OfficeLocation, RegularizationRequest, Holiday } from '@/services/attendance';
import { employeeService, EmployeeOption } from '@/services/employees';
import toast from 'react-hot-toast';

const STATUS_COLOR: Record<string, { bg: string; color: string; label: string; title: string }> = {
  present: { bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-500', color: 'text-emerald-500', label: 'P', title: 'Present' },
  late: { bg: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-500', color: 'text-yellow-500', label: 'L', title: 'Late' },
  half_day: { bg: 'bg-amber-500/10 border-amber-500/30 text-amber-500', color: 'text-amber-500', label: 'H', title: 'Half Day' },
  absent: { bg: 'bg-red-500/10 border-red-500/30 text-red-500', color: 'text-red-500', label: 'A', title: 'Absent / LOP' },
  pending: { bg: 'bg-orange-500/10 border-orange-500/30 text-orange-500', color: 'text-orange-500', label: 'PEN', title: 'Pending Correction' },
  missing: { bg: 'bg-slate-500/10 border-slate-500/30 text-slate-500', color: 'text-slate-500', label: 'M', title: 'Missing Punch' },
  leave: { bg: 'bg-purple-500/10 border-purple-500/30 text-purple-500', color: 'text-purple-500', label: 'LV', title: 'On Leave' },
  lop_leave: { bg: 'bg-rose-500/10 border-rose-500/30 text-rose-500', color: 'text-rose-500', label: 'LOP', title: 'LOP Leave' },
  holiday: { bg: 'bg-blue-500/10 border-blue-500/30 text-blue-500', color: 'text-blue-500', label: 'PH', title: 'Public Holiday' },
  weekend: { bg: 'bg-muted border-border text-muted-foreground', color: 'text-muted-foreground', label: 'W', title: 'Week Off' },
};

const roleLabel = (value?: string | null) =>
  String(value || 'employee')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());

const employeeLabel = (employee: EmployeeOption) => {
  const code = employee.emp_code ? ` (${employee.emp_code})` : '';
  return `${employee.display_name || `${employee.first_name} ${employee.last_name}`.trim() || employee.username}${code}`;
};

const attendanceValue = (employee: EmployeeOption) => employee.attendance_id || String(employee.user_id);

const dateInputValue = (value: Date) => {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

function haversineMetres(lat1: number, lon1: number, lat2: number, lon2: number) {
  const R = 6371000;
  const toRad = (d: number) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

function formatTime(val: string | null | undefined) {
  if (!val) return null;
  const match = val.match(/T?(\d{2}):(\d{2})/);
  if (match) return `${match[1]}:${match[2]}`;
  const d = new Date(val);
  if (!Number.isNaN(d.getTime())) {
    return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', hour12: false });
  }
  return String(val).slice(0, 5);
}

function parseCoordinate(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === '') return null;
  const parsed = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatLocation(latitude: number | string | null | undefined, longitude: number | string | null | undefined) {
  const lat = parseCoordinate(latitude);
  const lon = parseCoordinate(longitude);
  if (lat === null || lon === null) return null;
  return `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
}

function formatShiftLabel(shiftType?: string | null) {
  if (shiftType === 'night') return 'Night shift';
  if (shiftType === 'day') return 'Day shift';
  return 'Attendance';
}

function normalizeAttendanceRecord<T extends AttendanceRecord | null | undefined>(record: T): T {
  if (!record) return record;
  return {
    ...record,
    checkin_latitude: parseCoordinate(record.checkin_latitude),
    checkin_longitude: parseCoordinate(record.checkin_longitude),
    checkout_latitude: parseCoordinate(record.checkout_latitude),
    checkout_longitude: parseCoordinate(record.checkout_longitude),
  } as T;
}

function normalizeOfficeLocation(value: OfficeLocation | null | undefined): OfficeLocation | null {
  if (!value || value.configured === false) return null;
  const latitude = parseCoordinate(value.latitude);
  const longitude = parseCoordinate(value.longitude);
  if (latitude === null || longitude === null) return null;
  return {
    ...value,
    name: value.name || 'Head Office',
    latitude,
    longitude,
    radius_meters: Number(value.radius_meters) || 300,
  };
}

export function AttendancePage() {
  const { hasPermission, permissions, user } = usePermissions();

  const canViewOwnAttendance = hasPermission('ATTENDANCE_VIEW_ATTENDANCE');
  const canViewTeamAttendance = hasPermission('ATTENDANCE_VIEW_TEAM_ATTENDANCE');
  const canApproveRegularize = hasPermission('ATTENDANCE_APPROVE_REGULARIZE');

  const [tab, setTab] = useState<'today' | 'monthly' | 'requests' | 'approvals'>('today');

  // Core data states
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [todayData, setTodayData] = useState<any | null>(null);
  const [office, setOffice] = useState<OfficeLocation | null>(null);
  const [myAttendance, setMyAttendance] = useState<AttendanceRecord[]>([]);
  const [holidays, setHolidays] = useState<Holiday[]>([]);
  const [attendancePolicy, setAttendancePolicy] = useState<AttendancePolicy | null>(null);
  const [myRequests, setMyRequests] = useState<RegularizationRequest[]>([]);
  const [approvalsQueue, setApprovalsQueue] = useState<RegularizationRequest[]>([]);
  const [employees, setEmployees] = useState<EmployeeOption[]>([]);
  const [employeeFilter, setEmployeeFilter] = useState('');
  const [searchFilter, setSearchFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Hierarchical filter states matching screenshot
  const [selectedManagerId, setSelectedManagerId] = useState('');
  const [selectedTlId, setSelectedTlId] = useState('');
  const [selectedEmployeeId, setSelectedEmployeeId] = useState('');

  // Sub-states & loaders
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [actioningId, setActioningId] = useState<string | null>(null);
  const [approvalNote, setApprovalNote] = useState('');
  const [approvalsFilter, setApprovalsFilter] = useState<'pending' | 'approved' | 'rejected'>('pending');

  // Month-Year navigation for monthly log
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [dateFrom, setDateFrom] = useState(dateInputValue(new Date(now.getFullYear(), now.getMonth(), 1)));
  const [dateTo, setDateTo] = useState(dateInputValue(new Date(now.getFullYear(), now.getMonth() + 1, 0)));

  // GPS geolocation state
  const [gps, setGps] = useState<{ latitude: number; longitude: number; accuracy: number } | null>(null);
  const [locLoading, setLocLoading] = useState(false);
  const [locError, setLocError] = useState<string | null>(null);
  const [isWfh, setIsWfh] = useState(false);

  // Forms
  const [officeForm, setOfficeForm] = useState({ name: '', latitude: '', longitude: '', radius_meters: '300' });
  const currentAttendance = todayData?.record || null;
  const selectedEmployee = useMemo(
    () => employees.find((employee) => attendanceValue(employee) === employeeFilter),
    [employees, employeeFilter]
  );
  const selectedRoleLabel = selectedEmployee ? roleLabel(selectedEmployee.role) : 'Visible HRMS scope';
  const currentEmployeeLabel = selectedEmployee ? employeeLabel(selectedEmployee) : currentAttendance?.employee_name || 'My attendance';
  const currentEmployeeCode = selectedEmployee?.emp_code || currentAttendance?.emp_code || null;
  const currentShiftLabel = formatShiftLabel(currentAttendance?.shift_type);
  const [regularizeForm, setRegularizeForm] = useState({ date: '', check_in: '', check_out: '', reason: '' });
  const [showRegModal, setShowRegModal] = useState(false);

  const fetchGps = useCallback(() => {
    if (!navigator.geolocation) {
      setLocError('Geolocation is not supported by your browser.');
      return;
    }
    setLocLoading(true);
    setLocError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGps({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        });
        setLocLoading(false);
      },
      (err) => {
        const messages: Record<number, string> = {
          1: 'Location permission denied. Please allow location access and try again.',
          2: 'Location unavailable. Check your GPS/network.',
          3: 'Location request timed out. Try again.',
        };
        setLocError(messages[err.code] || 'Failed to get location.');
        setGps(null);
        setLocLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  }, []);

  const getFreshGps = useCallback((): Promise<{ latitude: number; longitude: number; accuracy: number } | null> => {
    if (isWfh || !office) return Promise.resolve(gps);
    if (!navigator.geolocation) {
      const message = 'Geolocation is not supported by your browser.';
      setLocError(message);
      toast.error(message);
      return Promise.resolve(null);
    }

    setLocLoading(true);
    setLocError(null);
    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const nextGps = {
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
          };
          setGps(nextGps);
          setLocLoading(false);
          resolve(nextGps);
        },
        (err) => {
          const messages: Record<number, string> = {
            1: 'Location permission denied. Please allow location access and try again.',
            2: 'Location unavailable. Check your GPS/network.',
            3: 'Location request timed out. Try again.',
          };
          const message = messages[err.code] || 'Failed to get location.';
          setLocError(message);
          setGps(null);
          setLocLoading(false);
          toast.error(message);
          resolve(null);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    });
  }, [gps, isWfh, office]);

  const loadData = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const employeesRes = await employeeService.list({
        search: searchFilter || undefined,
        active: true,
      });
      setEmployees(employeesRes.data || []);

      // 1. Today status
      const todayRes = await attendanceService.getToday();
      setTodayData({
        ...todayRes.data,
        record: normalizeAttendanceRecord(todayRes.data?.record),
      });
      setIsWfh(todayRes.data?.work_mode === 'work_from_home');

      // 2. Office location
      try {
        const officeRes = await attendanceService.getOfficeLocation();
        const normalizedOffice = normalizeOfficeLocation(officeRes.data);
        setOffice(normalizedOffice);
        if (normalizedOffice) {
          setOfficeForm({
            name: normalizedOffice.name,
            latitude: String(normalizedOffice.latitude),
            longitude: String(normalizedOffice.longitude),
            radius_meters: String(normalizedOffice.radius_meters),
          });
        }
      } catch {
        setOffice(null);
      }

      // 3. Holidays
      const holidaysRes = await attendanceService.getHolidays();
      setHolidays(holidaysRes.data || []);

      // 4. Requests (regularization)
      const myReqRes = await attendanceService.getMyRegularizations();
      setMyRequests(myReqRes.data || []);

      // 5. Monthly records
      const myAttRes = await attendanceService.getMyAttendance(month, year, employeeFilter || undefined);
      const myAttendancePayload = myAttRes.data as AttendanceRecord[] | { records?: AttendanceRecord[]; policy?: AttendancePolicy };
      const records = Array.isArray(myAttendancePayload) ? myAttendancePayload : myAttendancePayload?.records || [];
      setMyAttendance(records.map((record) => normalizeAttendanceRecord(record)));
      setAttendancePolicy(Array.isArray(myAttendancePayload) ? null : myAttendancePayload?.policy || null);

      // 6. Approvals (for managers)
      if (canApproveRegularize) {
        const appRes = await attendanceService.getAllRegularizations(approvalsFilter, employeeFilter || undefined);
        setApprovalsQueue(appRes.data || []);
      }
    } catch {
      toast.error('Could not load attendance data');
    } finally {
      setLoading(false);
    }
  };

  const gpsDistance = useMemo(() => {
    if (!gps || !office) return null;
    return haversineMetres(gps.latitude, gps.longitude, Number(office.latitude), Number(office.longitude));
  }, [gps, office]);

  const withinRadius = useMemo(() => {
    if (isWfh) return true;
    if (!office) return true;
    if (gpsDistance === null) return false;
    return gpsDistance <= office.radius_meters;
  }, [gpsDistance, office, isWfh]);

  const handleCheckIn = async () => {
    try {
      setSubmitting(true);
      const currentGps = await getFreshGps();
      if (!isWfh && office) {
        if (!currentGps) return;
        const distance = haversineMetres(currentGps.latitude, currentGps.longitude, Number(office.latitude), Number(office.longitude));
        if (distance > office.radius_meters) {
          toast.error('Cannot check-in: You are outside the allowed office perimeter.');
          return;
        }
      }
      await attendanceService.checkIn(isWfh, currentGps?.latitude ?? null, currentGps?.longitude ?? null);
      toast.success('Successfully checked in!');
      await loadData(true);
    } catch (err) {
      const errorMsg = (err as { response?: { data?: { error?: string } } }).response?.data?.error || 'Check-in failed';
      toast.error(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCheckOut = async () => {
    try {
      setSubmitting(true);
      if (!todayData?.record?.check_in || todayData?.record?.check_out) {
        toast.error('No open check-in found. Please check in first or refresh the page.');
        return;
      }
      const currentGps = await getFreshGps();
      if (!isWfh && office) {
        if (!currentGps) return;
        const distance = haversineMetres(currentGps.latitude, currentGps.longitude, Number(office.latitude), Number(office.longitude));
        if (distance > office.radius_meters) {
          toast.error('Cannot check-out: You are outside the allowed office perimeter.');
          return;
        }
      }
      const res = await attendanceService.checkOut(currentGps?.latitude ?? null, currentGps?.longitude ?? null);
      toast.success(`Checked out! Total hours: ${res.data.hours_worked || 0}h`);
      await loadData(true);
    } catch (err) {
      const errorMsg = (err as { response?: { data?: { error?: string } } }).response?.data?.error || 'Check-out failed';
      toast.error(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSaveOffice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!officeForm.name.trim() || !officeForm.latitude || !officeForm.longitude) {
      toast.error('Office name, latitude, and longitude are required');
      return;
    }
    try {
      setSubmitting(true);
      const payload: OfficeLocation = {
        name: officeForm.name,
        latitude: parseFloat(officeForm.latitude),
        longitude: parseFloat(officeForm.longitude),
        radius_meters: parseInt(officeForm.radius_meters) || 300,
      };
      await attendanceService.setOfficeLocation(payload);
      toast.success('Office coordinates updated successfully');
      await loadData(true);
    } catch {
      toast.error('Could not update office location');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRaiseRegularization = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regularizeForm.date || !regularizeForm.reason.trim()) {
      toast.error('Date and reason are required');
      return;
    }
    try {
      setSubmitting(true);
      const payload = {
        date: regularizeForm.date,
        requested_check_in: regularizeForm.check_in || undefined,
        requested_check_out: regularizeForm.check_out || undefined,
        reason: regularizeForm.reason,
      };
      await attendanceService.applyRegularization(payload);
      toast.success('Regularization request submitted!');
      setRegularizeForm({ date: '', check_in: '', check_out: '', reason: '' });
      setShowRegModal(false);
      await loadData(true);
    } catch (err) {
      const errorMsg = (err as { response?: { data?: { error?: string } } }).response?.data?.error || 'Failed to submit regularization request';
      toast.error(errorMsg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprovalAction = async (id: string, action: 'approve' | 'reject') => {
    try {
      setActioningId(id);
      await attendanceService.actionRegularization(id, action, approvalNote);
      toast.success(`Request successfully ${action}d`);
      setApprovalNote('');
      await loadData(true);
    } catch {
      toast.error('Approval operation failed');
    } finally {
      setActioningId(null);
    }
  };

  // Monthly Calendar construction helpers
  const daysInMonth = useMemo(() => new Date(year, month, 0).getDate(), [month, year]);
  const firstDayIndex = useMemo(() => new Date(year, month - 1, 1).getDay(), [month, year]);
  const calendarCells = useMemo(() => {
    const cells = [];
    for (let i = 0; i < firstDayIndex; i++) cells.push(null);
    for (let d = 1; d <= daysInMonth; d++) cells.push(d);
    return cells;
  }, [firstDayIndex, daysInMonth]);

  const monthName = useMemo(() => {
    return new Date(year, month - 1).toLocaleString('en-US', { month: 'long', year: 'numeric' });
  }, [month, year]);

  const officeMapUrl = useMemo(() => {
    if (!office) return '';
    const lat = Number(office.latitude);
    const lon = Number(office.longitude);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return '';
    const spread = 0.004;
    const bbox = [lon - spread, lat - spread, lon + spread, lat + spread].join('%2C');
    return `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat}%2C${lon}`;
  }, [office]);
  const checkinLocation = formatLocation(todayData?.record?.checkin_latitude, todayData?.record?.checkin_longitude);
  const checkoutLocation = formatLocation(todayData?.record?.checkout_latitude, todayData?.record?.checkout_longitude);

  const attendanceLookup = useMemo(() => {
    const map: Record<string, AttendanceRecord> = {};
    myAttendance.filter((rec) => {
      if (dateFrom && rec.date < dateFrom) return false;
      if (dateTo && rec.date > dateTo) return false;
      if (statusFilter === 'missing') {
        return rec.pending_reason === 'missing_attendance' || rec.pending_reason === 'missing_checkout' || Boolean(rec.check_in && !rec.check_out);
      }
      if (statusFilter) return rec.status === statusFilter;
      return true;
    }).forEach((rec) => {
      map[rec.date] = rec;
    });
    return map;
  }, [dateFrom, dateTo, myAttendance, statusFilter]);

  const weekendDays = useMemo(
    () => new Set((attendancePolicy?.weekend_days || ['saturday', 'sunday']).map((day) => day.toLowerCase())),
    [attendancePolicy]
  );

  const isWeekendDate = useCallback(
    (value: Date) => {
      const names = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
      return weekendDays.has(names[value.getDay()]);
    },
    [weekendDays]
  );

  const holidayLookup = useMemo(() => {
    const map: Record<string, string> = {};
    holidays.forEach((h) => {
      map[h.date] = h.name;
    });
    return map;
  }, [holidays]);

  const handlePrevMonth = () => {
    if (month === 1) {
      setMonth(12);
      setYear((y) => y - 1);
      syncDateRangeToMonth(12, year - 1);
    } else {
      setMonth((m) => m - 1);
      syncDateRangeToMonth(month - 1, year);
    }
  };

  const handleNextMonth = () => {
    if (month === 12) {
      setMonth(1);
      setYear((y) => y + 1);
      syncDateRangeToMonth(1, year + 1);
    } else {
      setMonth((m) => m + 1);
      syncDateRangeToMonth(month + 1, year);
    }
  };

  const syncDateRangeToMonth = (nextMonth: number, nextYear: number) => {
    setDateFrom(dateInputValue(new Date(nextYear, nextMonth - 1, 1)));
    setDateTo(dateInputValue(new Date(nextYear, nextMonth, 0)));
  };

  const applyFilters = () => {
    if (dateFrom) {
      const parsed = new Date(`${dateFrom}T00:00:00`);
      if (!Number.isNaN(parsed.getTime())) {
        setMonth(parsed.getMonth() + 1);
        setYear(parsed.getFullYear());
      }
    }
    loadData(true);
  };

  // Dynamic role groups & permissions mapping from backend
  const userRole = (user?.role || '').toLowerCase();
  
  const getRoleGroup = (employeeOrRole: EmployeeOption | string) => {
    const r = typeof employeeOrRole === 'string'
      ? String(employeeOrRole || '').toLowerCase()
      : [
          employeeOrRole.base_role,
          employeeOrRole.role,
          employeeOrRole.designation,
        ].filter(Boolean).join(' ').toLowerCase();
    if (r.includes('super') || r.includes('admin')) return 'admin';
    if (r.includes('hr') || r.includes('human')) return 'hr';
    if (r.includes('manager') || r.includes('head') || r.includes('director')) return 'manager';
    if (r.includes('leader') || r.includes('lead') || r.includes('tl') || r.includes('teamleader')) return 'tl';
    return 'employee';
  };

  const isSuperAdmin = ['super_admin', 'superadmin', 'platform_admin', 'system_admin'].includes(userRole) || permissions.includes('*');
  const isHr = !isSuperAdmin && ['hr', 'hr_manager', 'hr_executive', 'hr manager'].includes(userRole);
  const isManager = !isSuperAdmin && !isHr && (userRole.includes('manager') || ['dept_head', 'department_head'].includes(userRole));
  const isTl = !isSuperAdmin && !isHr && !isManager && (userRole.includes('leader') || userRole.includes('lead') || ['tl', 'teamleader'].includes(userRole));
  const isEmployee = !isSuperAdmin && !isHr && !isManager && !isTl;

  const resetFilters = () => {
    setSelectedManagerId('');
    setSelectedTlId('');
    setSelectedEmployeeId('');
    setEmployeeFilter('');
    setSearchFilter('');
    setStatusFilter('');
    syncDateRangeToMonth(month, year);
  };

  useEffect(() => {
    loadData();
  }, [month, year, approvalsFilter, employeeFilter, searchFilter]);

  const selectedManagerUserId = useMemo(() => {
    const selected = employees.find((employee) => attendanceValue(employee) === selectedManagerId);
    return selected?.user_id;
  }, [employees, selectedManagerId]);

  const selectedTlUserId = useMemo(() => {
    const selected = employees.find((employee) => attendanceValue(employee) === selectedTlId);
    return selected?.user_id;
  }, [employees, selectedTlId]);

  // Hierarchical lists matching active selections & role limits
  const visibleManagers = useMemo(() => {
    return employees.filter((emp) => ['manager', 'hr'].includes(getRoleGroup(emp)));
  }, [employees]);

  const visibleTls = useMemo(() => {
    let list = employees.filter((emp) => getRoleGroup(emp) === 'tl');
    if (isManager && user?.id) {
      list = list.filter((emp) => emp.manager === user.id);
    } else if (selectedManagerUserId) {
      list = list.filter((emp) => emp.manager === selectedManagerUserId);
    }
    return list;
  }, [employees, isManager, user?.id, selectedManagerUserId]);

  const visibleEmployees = useMemo(() => {
    let list = employees.filter((emp) => {
      const group = getRoleGroup(emp);
      return group !== 'manager' && group !== 'hr' && group !== 'tl' && group !== 'admin';
    });

    if (isTl && user?.id) {
      list = list.filter((emp) => emp.manager === user.id);
    } else if (selectedTlUserId) {
      list = list.filter((emp) => emp.manager === selectedTlUserId);
    } else if (selectedManagerUserId) {
      const tlsUnderManager = visibleTls.map(t => t.user_id);
      list = list.filter((emp) => emp.manager === selectedManagerUserId || tlsUnderManager.includes(emp.manager || 0));
    } else if (isManager && user?.id) {
      const tlsUnderManager = visibleTls.map(t => t.user_id);
      list = list.filter((emp) => emp.manager === user.id || tlsUnderManager.includes(emp.manager || 0));
    }
    return list;
  }, [employees, isTl, isManager, user?.id, selectedTlUserId, selectedManagerUserId, visibleTls]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Attendance & Check-in"
        description="Verify your position, check in/out, view timesheets, and apply for corrections."
        actions={
          <Button size="sm" onClick={() => loadData()} disabled={loading} className="flex items-center gap-1.5">
            <RefreshCw className={cn('h-4 w-4', loading && 'animate-spin')} />
            Refresh Data
          </Button>
        }
      />

      <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
        <span className="rounded-full border bg-muted/40 px-3 py-1 font-semibold text-foreground">{currentEmployeeLabel}</span>
        {currentEmployeeCode && <span className="rounded-full border bg-muted/20 px-3 py-1 font-mono">{currentEmployeeCode}</span>}
        <span className="rounded-full border border-primary/20 bg-primary/10 px-3 py-1 font-semibold text-primary">
          {employeeFilter ? selectedRoleLabel : currentShiftLabel}
        </span>
      </div>

      {/* Premium Horizontal Filter Bar matching reference screenshot */}
      {!isEmployee && (
        <Card className="border-border/80 bg-card/60 backdrop-blur-sm shadow-sm mb-6">
          <CardContent className="p-3 flex flex-wrap items-center gap-3">
            {/* Filter icon label */}
            <div className="flex items-center gap-1.5 px-3 h-9 rounded-lg bg-primary/10 text-primary border border-primary/20">
              <Filter className="h-3.5 w-3.5" />
              <span className="text-xs font-bold uppercase tracking-wider">Filters</span>
            </div>

            {/* Managers / HR select (SuperAdmin / HR only) */}
            {(isSuperAdmin || isHr) && (
              <select
                value={selectedManagerId}
                onChange={(e) => {
                  const val = e.target.value;
                  setSelectedManagerId(val);
                  setSelectedTlId('');
                  setSelectedEmployeeId('');
                  setEmployeeFilter(val);
                }}
                className="h-9 rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground font-semibold outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all cursor-pointer min-w-[150px]"
              >
                <option value="">MANAGERS / HR</option>
                {visibleManagers.map((m) => (
                  <option key={m.user_id} value={attendanceValue(m)}>
                    {m.display_name || `${m.first_name} ${m.last_name}`.trim() || m.username}
                  </option>
                ))}
              </select>
            )}

            {/* Team Leaders select */}
            {(isSuperAdmin || isHr || isManager) && (
              <select
                value={selectedTlId}
                onChange={(e) => {
                  const val = e.target.value;
                  setSelectedTlId(val);
                  setSelectedEmployeeId('');
                  setEmployeeFilter(val || selectedManagerId);
                }}
                className="h-9 rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground font-semibold outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all cursor-pointer min-w-[150px]"
              >
                <option value="">TEAM LEADERS</option>
                {visibleTls.map((t) => (
                  <option key={t.user_id} value={attendanceValue(t)}>
                    {t.display_name || `${t.first_name} ${t.last_name}`.trim() || t.username}
                  </option>
                ))}
              </select>
            )}

            {/* Employees select */}
            {(isSuperAdmin || isHr || isManager || isTl) && (
              <select
                value={selectedEmployeeId}
                onChange={(e) => {
                  const val = e.target.value;
                  setSelectedEmployeeId(val);
                  setEmployeeFilter(val || selectedTlId || selectedManagerId);
                }}
                className="h-9 rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground font-semibold outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all cursor-pointer min-w-[150px]"
              >
                <option value="">EMPLOYEES</option>
                {visibleEmployees.map((a) => (
                  <option key={a.user_id} value={attendanceValue(a)}>
                    {a.display_name || `${a.first_name} ${a.last_name}`.trim() || a.username}
                  </option>
                ))}
              </select>
            )}

            {/* Date From */}
            <div className="flex items-center gap-2 border border-border rounded-lg px-2.5 h-9 bg-background focus-within:border-primary focus-within:ring-1 focus-within:ring-primary/30 transition-all">
              <CalendarDays className="h-3.5 w-3.5 text-muted-foreground" />
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="bg-transparent text-xs text-foreground font-semibold outline-none w-28 cursor-pointer"
              />
            </div>

            {/* Date To */}
            <div className="flex items-center gap-2 border border-border rounded-lg px-2.5 h-9 bg-background focus-within:border-primary focus-within:ring-1 focus-within:ring-primary/30 transition-all">
              <CalendarDays className="h-3.5 w-3.5 text-muted-foreground" />
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="bg-transparent text-xs text-foreground font-semibold outline-none w-28 cursor-pointer"
              />
            </div>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-9 rounded-lg border border-border bg-background px-3 py-1.5 text-xs text-foreground font-semibold outline-none focus:border-primary focus:ring-1 focus:ring-primary/30 transition-all cursor-pointer min-w-[130px]"
            >
              <option value="">STATUS</option>
              <option value="present">Present</option>
              <option value="late">Late</option>
              <option value="half_day">Half day</option>
              <option value="pending">Pending</option>
              <option value="missing">Missing Punch</option>
              <option value="leave">Leave</option>
              <option value="holiday">Holiday</option>
            </select>

            {/* Search Filter */}
            <div className="flex items-center gap-2 border border-border rounded-lg px-2.5 h-9 bg-background focus-within:border-primary focus-within:ring-1 focus-within:ring-primary/30 transition-all min-w-[150px] max-w-[200px]">
              <Search className="h-3.5 w-3.5 text-muted-foreground" />
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') applyFilters();
                }}
                placeholder="Search..."
                className="bg-transparent text-xs text-foreground font-semibold outline-none w-full"
              />
            </div>

            {/* RESET button */}
            <button
              type="button"
              onClick={resetFilters}
              className="text-xs font-bold text-muted-foreground hover:text-foreground transition-all uppercase cursor-pointer hover:underline px-2"
            >
              Reset
            </button>

            {/* UPDATE button */}
            <Button
              size="sm"
              onClick={applyFilters}
              disabled={loading}
              className="h-9 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-lg px-4 flex items-center gap-1.5 transition-all shadow-sm active:scale-95 ml-auto"
            >
              <RefreshCw className={cn('h-3.5 w-3.5', loading && 'animate-spin')} />
              Update
            </Button>
        </CardContent>
      </Card>
      )}

      <div className="min-w-0 space-y-6">

      {/* Tabs */}
      <div className="flex p-1 bg-muted rounded-xl w-fit border border-border">
        <button
          onClick={() => setTab('today')}
          className={cn(
            'px-4 py-2 rounded-lg text-xs font-semibold transition-all active:scale-95',
            tab === 'today' ? 'bg-card text-foreground shadow-sm border border-border' : 'text-muted-foreground hover:text-foreground'
          )}
        >
          📍 Today
        </button>
        <button
          onClick={() => setTab('monthly')}
          className={cn(
            'px-4 py-2 rounded-lg text-xs font-semibold transition-all active:scale-95',
            tab === 'monthly' ? 'bg-card text-foreground shadow-sm border border-border' : 'text-muted-foreground hover:text-foreground'
          )}
        >
          📅 Monthly Records
        </button>
        <button
          onClick={() => setTab('requests')}
          className={cn(
            'px-4 py-2 rounded-lg text-xs font-semibold transition-all active:scale-95',
            tab === 'requests' ? 'bg-card text-foreground shadow-sm border border-border' : 'text-muted-foreground hover:text-foreground'
          )}
        >
          📝 My Requests
        </button>
        {canApproveRegularize && (
          <button
            onClick={() => setTab('approvals')}
            className={cn(
              'px-4 py-2 rounded-lg text-xs font-semibold transition-all active:scale-95',
              tab === 'approvals' ? 'bg-card text-foreground shadow-sm border border-border' : 'text-muted-foreground hover:text-foreground'
            )}
          >
            ✅ Approvals Queue
          </button>
        )}
      </div>

      {loading && !todayData ? (
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          {/* TAB 1: TODAY CHECK-IN / CHECK-OUT */}
          {tab === 'today' && (
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2 space-y-6">
                <Card>
                  <CardContent className="space-y-6">
                    {/* Geolocation Coordinate Inspector Card */}
                    {false && !isWfh && office && (
                      <Card className="bg-muted/20 border-dashed">
                        <CardContent className="p-4 space-y-3">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-semibold text-muted-foreground">Geofencing perimeter validation</span>
                            {locLoading ? (
                              <span className="flex items-center gap-1 text-primary">
                                <Loader2 className="h-3.5 w-3.5 animate-spin" /> Fetching location...
                              </span>
                            ) : gps ? (
                              <Badge variant={withinRadius ? 'success' : 'destructive'} className="text-[10px]">
                                {withinRadius ? 'Within Range' : 'Out of Bounds'}
                              </Badge>
                            ) : (
                              <span className="text-destructive font-semibold">Location Unknown</span>
                            )}
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                            <div className="p-2.5 bg-background border rounded-lg space-y-1">
                              <p className="text-[10px] font-bold text-muted-foreground uppercase">Target Office Location</p>
                              <p className="font-mono text-[11px] text-foreground font-semibold">{office!.name}</p>
                              <p className="font-mono text-[10px] text-muted-foreground">
                                Coordinates: {Number(office!.latitude).toFixed(6)}, {Number(office!.longitude).toFixed(6)}
                              </p>
                              <p className="font-mono text-[10px] text-muted-foreground">Geofence Radius: {office!.radius_meters}m</p>
                            </div>

                            <div className="p-2.5 bg-background border rounded-lg space-y-1">
                              <p className="text-[10px] font-bold text-muted-foreground uppercase">Your Current GPS Position</p>
                              {gps ? (
                                <>
                                  <p className="font-mono text-[11px] text-foreground font-semibold">
                                    {gps!.latitude.toFixed(6)}, {gps!.longitude.toFixed(6)}
                                  </p>
                                  <p className="font-mono text-[10px] text-muted-foreground">Accuracy: ±{Math.round(gps!.accuracy)}m</p>
                                  {gpsDistance !== null && (
                                    <p className="font-mono text-[10px] text-primary font-semibold">
                                      Distance: {Math.round(gpsDistance!)}m from center
                                    </p>
                                  )}
                                </>
                              ) : (
                                <p className="text-muted-foreground italic text-[11px]">No GPS coordinate lock acquired.</p>
                              )}
                            </div>
                          </div>

                          {locError && (
                            <div className="flex gap-1.5 text-xs text-yellow-500 bg-yellow-500/5 p-2.5 rounded-lg border border-yellow-500/20">
                              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                              <div>
                                <p className="font-semibold">GPS Error Lock Alert</p>
                                <p className="text-[10px] text-yellow-500/80">{locError}</p>
                              </div>
                            </div>
                          )}

                          <Button
                            size="sm"
                            variant="outline"
                            onClick={fetchGps}
                            disabled={locLoading}
                            className="w-full text-xs flex items-center justify-center gap-1.5"
                          >
                            <MapPin className="h-3.5 w-3.5" />
                            Force GPS Coordinate Refresh
                          </Button>
                        </CardContent>
                      </Card>
                    )}

                    {/* Clock buttons */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 border rounded-xl bg-muted/10 space-y-2 text-xs">
                        <p className="font-semibold text-muted-foreground flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5 text-emerald-500" />
                          Check-In Time
                        </p>
                        <p className="text-xl font-bold text-foreground">
                          {todayData?.record?.check_in ? formatTime(todayData.record.check_in) : '--:--'}
                        </p>
                        <p className="text-[10px] text-muted-foreground">
                          {checkinLocation
                            ? `Location logged: ${checkinLocation}`
                            : isWfh
                              ? 'Logged as Remote check-in'
                              : 'No clock-in captured yet.'}
                        </p>
                      </div>

                      <div className="p-4 border rounded-xl bg-muted/10 space-y-2 text-xs">
                        <p className="font-semibold text-muted-foreground flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5 text-rose-500" />
                          Check-Out Time
                        </p>
                        <p className="text-xl font-bold text-foreground">
                          {todayData?.record?.check_out ? formatTime(todayData.record.check_out) : '--:--'}
                        </p>
                        <p className="text-[10px] text-muted-foreground">
                          {checkoutLocation
                            ? `Location logged: ${checkoutLocation}`
                            : 'No clock-out captured yet.'}
                        </p>
                      </div>
                    </div>

                    {/* Checkin / Checkout buttons triggers */}
                    {!todayData?.record?.check_in ? (
                      <Button
                        onClick={handleCheckIn}
                        disabled={submitting || (!isWfh && !!office && locLoading)}
                        className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold h-12 flex items-center justify-center gap-1.5"
                      >
                        {submitting && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                        Check-in (Punch Work Start)
                      </Button>
                    ) : !todayData?.record?.check_out ? (
                      <Button
                        onClick={handleCheckOut}
                        disabled={submitting || (!isWfh && !!office && locLoading)}
                        className="w-full bg-rose-600 hover:bg-rose-700 text-white font-bold h-12 flex items-center justify-center gap-1.5"
                      >
                        {submitting && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                        Check-out (Punch Work Finish)
                      </Button>
                    ) : (
                      <div className="text-center p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-500 rounded-xl space-y-1">
                        <CheckCircle2 className="h-6 w-6 mx-auto mb-1 text-emerald-500" />
                        <p className="text-xs font-semibold">Today's Clock punches are complete!</p>
                        <p className="text-[10px] text-emerald-500/70">
                          Total Hours: {todayData.record.hours_worked}h | Overtime: {todayData.record.ot_hours}h
                        </p>
                      </div>
                    )}

                    <div className="text-center">
                      <button
                        onClick={() => {
                          setRegularizeForm({
                            date: todayData?.record?.date || new Date().toISOString().split('T')[0],
                            check_in: todayData?.record?.check_in ? formatTime(todayData.record.check_in) || '' : '',
                            check_out: todayData?.record?.check_out ? formatTime(todayData.record.check_out) || '' : '',
                            reason: '',
                          });
                          setShowRegModal(true);
                        }}
                        className="text-xs text-primary underline hover:text-primary/80"
                      >
                        Missed a punch clock register? Apply for Regularization correction
                      </button>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Office Location perimeter configuration */}
              <div className="space-y-6">
                {false && canViewTeamAttendance && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Configure Office Center Geofence</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <form onSubmit={handleSaveOffice} className="space-y-4 text-xs">
                        <div className="space-y-1.5">
                          <label className="font-semibold text-muted-foreground">Office Center Name</label>
                          <Input
                            value={officeForm.name}
                            onChange={(e) => setOfficeForm((p) => ({ ...p, name: e.target.value }))}
                            placeholder="e.g. Headquarters Office"
                            required
                          />
                        </div>

                        <div className="space-y-1.5">
                          <label className="font-semibold text-muted-foreground">Center Latitude Coordinates</label>
                          <Input
                            value={officeForm.latitude}
                            onChange={(e) => setOfficeForm((p) => ({ ...p, latitude: e.target.value }))}
                            placeholder="e.g. 12.971598"
                            required
                          />
                        </div>

                        <div className="space-y-1.5">
                          <label className="font-semibold text-muted-foreground">Center Longitude Coordinates</label>
                          <Input
                            value={officeForm.longitude}
                            onChange={(e) => setOfficeForm((p) => ({ ...p, longitude: e.target.value }))}
                            placeholder="e.g. 77.594562"
                            required
                          />
                        </div>

                        <div className="space-y-1.5">
                          <label className="font-semibold text-muted-foreground">Perimeter Zone Radius (Meters)</label>
                          <Input
                            type="number"
                            value={officeForm.radius_meters}
                            onChange={(e) => setOfficeForm((p) => ({ ...p, radius_meters: e.target.value }))}
                            placeholder="e.g. 100"
                            required
                          />
                        </div>

                        <Button type="submit" disabled={submitting} className="w-full flex items-center justify-center gap-1.5">
                          {submitting && <Loader2 className="h-3 w-3 animate-spin" />}
                          Save Geofencing Rules
                        </Button>
                      </form>
                    </CardContent>
                  </Card>
                )}

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">System Settings Location Map</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4 text-xs">
                    {office && officeMapUrl ? (
                      <>
                        <div className="relative h-64 overflow-hidden rounded-xl border bg-muted">
                          <iframe
                            title="Office geofence map"
                            src={officeMapUrl}
                            className="h-full w-full"
                            loading="lazy"
                          />
                          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                            <div className="h-32 w-32 rounded-full border-2 border-primary bg-primary/10 shadow-[0_0_0_999px_rgba(255,255,255,0.02)]" />
                          </div>
                          <div className="absolute left-3 top-3 rounded-lg border bg-background/95 px-3 py-2 shadow-sm">
                            <p className="font-semibold text-foreground">{office.name || 'Head Office'}</p>
                            <p className="text-[10px] text-muted-foreground">
                              Allowed radius: {office.radius_meters || 300} meters
                            </p>
                          </div>
                        </div>

                        <div className="grid gap-3">
                          <div className="flex items-center justify-between border-b pb-2">
                            <span className="text-muted-foreground font-medium">System Setting Coordinates</span>
                            <span className="font-mono text-[10px] font-bold text-foreground">
                              {Number(office.latitude).toFixed(6)}, {Number(office.longitude).toFixed(6)}
                            </span>
                          </div>
                          <div className="flex items-center justify-between border-b pb-2">
                            <span className="text-muted-foreground font-medium">Your Distance</span>
                            <span className={cn('font-bold', withinRadius ? 'text-emerald-600' : 'text-rose-600')}>
                              {gpsDistance === null ? 'Waiting for GPS' : `${Math.round(gpsDistance)} meters`}
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground font-medium">Check-in Permission</span>
                            <Badge variant={withinRadius ? 'success' : 'destructive'}>
                              {withinRadius ? 'Allowed' : 'Blocked'}
                            </Badge>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="rounded-xl border border-dashed p-6 text-center text-muted-foreground">
                        Office latitude and longitude are not configured in system settings.
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {/* TAB 2: MONTHLY VIEW CALENDAR GRID */}
          {tab === 'monthly' && (
            <Card>
              <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-4">
                <CardTitle className="text-base">Attendance Calendar Sheet</CardTitle>

                {/* Calendar month selector controls */}
                <div className="flex items-center gap-3">
                  <Button size="icon" variant="outline" onClick={handlePrevMonth} className="h-8 w-8">
                    &lt;
                  </Button>
                  <span className="font-bold text-xs w-28 text-center">{monthName}</span>
                  <Button size="icon" variant="outline" onClick={handleNextMonth} className="h-8 w-8">
                    &gt;
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Legend colors */}
                <div className="flex flex-wrap items-center gap-2 text-[10px] text-muted-foreground border-b pb-3 border-border">
                  {Object.entries(STATUS_COLOR).map(([key, val]) => (
                    <div key={key} className="flex items-center gap-1 border px-2 py-1 rounded bg-muted/10">
                      <span className={cn('h-2.5 w-2.5 rounded-sm', key === 'weekend' ? 'bg-muted border border-border' : 'bg-current', val.color)} />
                      <span className="font-medium">{val.title}</span>
                    </div>
                  ))}
                  <div className="flex items-center gap-1 border px-2 py-1 rounded bg-muted/10">
                    <span className="h-2.5 w-2.5 rounded-sm bg-purple-500/10 border border-purple-500/30" />
                    <span className="font-medium text-purple-500">Overtime (OT)</span>
                  </div>
                </div>
                {attendancePolicy && (
                  <div className="grid gap-2 rounded-lg border bg-muted/10 p-3 text-[10px] text-muted-foreground sm:grid-cols-5">
                    <span>Shift: <b className="text-foreground">{attendancePolicy.shift_start} - {attendancePolicy.shift_end}</b></span>
                    {attendancePolicy.night_shift_enabled && (
                      <span>Night: <b className="text-foreground">{attendancePolicy.night_shift_start} - {attendancePolicy.night_shift_end}</b></span>
                    )}
                    <span>Grace: <b className="text-foreground">{attendancePolicy.grace_minutes} min</b></span>
                    <span>Half day below: <b className="text-foreground">{attendancePolicy.half_day_hours}h</b></span>
                    <span>Weekends: <b className="text-foreground">{attendancePolicy.weekend_days?.join(', ') || 'none'}</b></span>
                  </div>
                )}

                {/* Calendar Grid */}
                <div className="border rounded-xl overflow-hidden bg-card text-xs">
                  {/* Headers */}
                  <div className="grid grid-cols-7 border-b bg-muted/40 font-semibold text-center text-muted-foreground">
                    {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d, index) => {
                      const names = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
                      const isWeekendDay = weekendDays.has(names[index]);
                      return (
                        <div key={d} className={cn('py-2 border-r last:border-r-0', isWeekendDay && 'bg-muted/70')}>
                          {d}
                        </div>
                      );
                    })}
                  </div>

                  {/* Cell days */}
                  <div className="grid grid-cols-7 grid-flow-row">
                    {calendarCells.map((day, cellIndex) => {
                      if (!day) return <div key={`empty-${cellIndex}`} className="min-h-[70px] border-r border-b bg-muted/20" />;

                      const dateString = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                      const record = attendanceLookup[dateString];
                      const holidayName = holidayLookup[dateString] || record?.holiday_name;

                      const cellDate = new Date(dateString);
                      const isWeekendDay = isWeekendDate(cellDate);
                      const cellToday = dateString === new Date().toISOString().split('T')[0];

                      let statusKey = record?.status;
                      if (record && !record.check_out && !['leave', 'lop_leave', 'holiday'].includes(record.status) && dateString !== new Date().toISOString().split('T')[0]) {
                        statusKey = 'missing';
                      }
                      if (record?.pending_reason === 'missing_attendance' || record?.pending_reason === 'missing_checkout') {
                        statusKey = 'missing';
                      }

                      let displayColor = STATUS_COLOR.weekend;
                      if (record) {
                        displayColor = STATUS_COLOR[statusKey || ''] || STATUS_COLOR.absent;
                      } else if (holidayName) {
                        displayColor = STATUS_COLOR.holiday;
                      }

                      const hasOT = record && record.check_in && record.check_out && record.ot_hours > 0;
                      const checkInFormatted = record?.check_in ? formatTime(record.check_in) : null;
                      const checkOutFormatted = record?.check_out ? formatTime(record.check_out) : null;

                      return (
                        <div
                          key={day}
                          onClick={() => {
                            if (employeeFilter) return;
                            if (isWeekendDay || holidayName) return;
                            setRegularizeForm({
                              date: dateString,
                              check_in: checkInFormatted || '',
                              check_out: checkOutFormatted || '',
                              reason: '',
                            });
                            setShowRegModal(true);
                          }}
                          className={cn(
                            'min-h-[75px] border-r border-b p-1.5 flex flex-col justify-between hover:bg-muted/30 cursor-pointer transition-colors',
                            cellToday && 'bg-primary/5 ring-1 ring-primary/30 ring-inset'
                          )}
                        >
                          {/* Date and tags */}
                          <div className="flex items-center justify-between">
                            <span className={cn('font-bold', cellToday && 'text-primary')}>{day}</span>
                            <div className="flex gap-0.5">
                              {holidayName && <Badge className="text-[8px] bg-blue-500/10 border-blue-500/30 text-blue-500 py-0 px-1">PH</Badge>}
                              {record && <Badge className={cn('text-[8px] py-0 px-1', displayColor.bg)}>{displayColor.label}</Badge>}
                            </div>
                          </div>

                          {/* Detail information inside cell */}
                          <div className="mt-1 space-y-0.5">
                            <div className="flex flex-wrap items-center gap-1">
                              <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-1.5 py-0.5 text-[8px] font-semibold uppercase text-emerald-600">
                                In
                              </span>
                              <p className="text-[9px] text-foreground font-medium">{checkInFormatted || '--:--'}</p>
                            </div>
                            <div className="flex flex-wrap items-center gap-1">
                              <span className="rounded-full border border-rose-500/20 bg-rose-500/10 px-1.5 py-0.5 text-[8px] font-semibold uppercase text-rose-600">
                                Out
                              </span>
                              <p className="text-[9px] text-foreground font-medium">{checkOutFormatted || '--:--'}</p>
                            </div>
                            {hasOT && (
                              <p className="text-[8px] text-purple-500 font-bold">
                                OT +{record?.ot_hours}h
                              </p>
                            )}
                            {statusKey === 'late' && (
                              <p className="text-[8px] text-yellow-500 font-semibold">Late entry</p>
                            )}
                            {holidayName && (
                              <p className="text-[8px] text-blue-500 font-medium truncate max-w-full">{holidayName}</p>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* TAB 3: MY REQUESTS (REGULARIZATION LIST) */}
          {tab === 'requests' && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-base">Correction Submissions Log</CardTitle>
                <Button
                  size="sm"
                  disabled={Boolean(employeeFilter)}
                  onClick={() => {
                    setRegularizeForm({
                      date: new Date().toISOString().split('T')[0],
                      check_in: '',
                      check_out: '',
                      reason: '',
                    });
                    setShowRegModal(true);
                  }}
                  className="flex items-center gap-1.5"
                >
                  Apply Correction
                </Button>
              </CardHeader>
              <CardContent>
                {myRequests.length === 0 ? (
                  <div className="text-center py-12 text-xs text-muted-foreground border-dashed border-2 rounded-xl">
                    No regularization correction applications filed.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {myRequests.map((req) => (
                      <div key={req.id} className="border p-4 rounded-xl text-xs space-y-2 bg-muted/20">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-foreground text-sm">{req.date}</span>
                          <Badge
                            variant={req.status === 'approved' ? 'success' : req.status === 'rejected' ? 'destructive' : 'warning'}
                          >
                            {req.status}
                          </Badge>
                        </div>
                        <p className="text-muted-foreground">
                          Requested Corrections: <strong className="text-foreground">{req.requested_check_in || '—'} → {req.requested_check_out || '—'}</strong>
                        </p>
                        <p className="text-muted-foreground">
                          Reason: <span className="text-foreground">{req.reason}</span>
                        </p>
                        {req.manager_note && (
                          <div className="bg-background border rounded-lg p-2 mt-1 text-[11px] text-yellow-500/80">
                            <strong>Approver's Feedback:</strong> {req.manager_note}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* TAB 4: APPROVALS QUEUE (MANAGERS ONLY) */}
          {tab === 'approvals' && (
            <Card>
              <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-4">
                <CardTitle className="text-base">Regularization Queue Reviews</CardTitle>

                {/* Filter button triggers */}
                <div className="flex gap-1 bg-muted p-0.5 rounded-lg border text-xs">
                  {(['pending', 'approved', 'rejected'] as const).map((filterOpt) => (
                    <button
                      key={filterOpt}
                      onClick={() => setApprovalsFilter(filterOpt)}
                      className={cn(
                        'px-3 py-1.5 rounded-md font-semibold capitalize transition-all',
                        approvalsFilter === filterOpt ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
                      )}
                    >
                      {filterOpt}
                    </button>
                  ))}
                </div>
              </CardHeader>
              <CardContent>
                {approvalsQueue.length === 0 ? (
                  <div className="text-center py-12 text-xs text-muted-foreground">
                    No regularization requests in this category.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {approvalsQueue.map((req) => (
                      <div key={req.id} className="border p-4 rounded-xl text-xs space-y-3 bg-muted/20">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                          <div>
                            <span className="font-bold text-foreground text-sm">{req.employee_name}</span>
                            <span className="text-muted-foreground mx-2">•</span>
                            <span className="text-muted-foreground">Date: {req.date}</span>
                          </div>
                          <Badge
                            variant={req.status === 'approved' ? 'success' : req.status === 'rejected' ? 'destructive' : 'warning'}
                          >
                            {req.status}
                          </Badge>
                        </div>

                        <div className="space-y-1.5 p-3 bg-background border rounded-lg">
                          <p className="text-muted-foreground">
                            Correction Request: <strong className="text-foreground">{req.requested_check_in || '—'} → {req.requested_check_out || '—'}</strong>
                          </p>
                          <p className="text-muted-foreground">
                            Employee Justification: <span className="text-foreground">{req.reason}</span>
                          </p>
                        </div>

                        {req.status === 'pending' && req.employee_id !== String(user?.id) && (
                          <div className="space-y-2.5 pt-2 border-t">
                            <div className="space-y-1.5">
                              <label className="font-semibold text-muted-foreground">Resolution Note / feedback</label>
                              <Input
                                value={approvalNote}
                                onChange={(e) => setApprovalNote(e.target.value)}
                                placeholder="Explain approval/rejection details (optional)..."
                              />
                            </div>
                            <div className="flex gap-2 justify-end">
                              <Button
                                size="sm"
                                variant="outline"
                                className="bg-red-500/10 hover:bg-red-500/20 text-red-500 border-red-500/20"
                                onClick={() => handleApprovalAction(req.id, 'reject')}
                                disabled={Boolean(actioningId)}
                              >
                                {actioningId === req.id && <Loader2 className="h-3 w-3 animate-spin mr-1" />}
                                Reject Request
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => handleApprovalAction(req.id, 'approve')}
                                disabled={Boolean(actioningId)}
                              >
                                {actioningId === req.id && <Loader2 className="h-3 w-3 animate-spin mr-1" />}
                                Approve & Correction
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}
      </div>

      {/* REGULARIZATION FORM DIALOG MODAL */}
      {showRegModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs">
          <Card className="w-full max-w-md mx-4">
            <CardHeader className="flex flex-row items-center justify-between pb-3 border-b">
              <CardTitle className="text-base">Apply Attendance Correction</CardTitle>
              <button onClick={() => setShowRegModal(false)} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </CardHeader>
            <CardContent className="pt-4">
              <form onSubmit={handleRaiseRegularization} className="space-y-4 text-xs">
                <div className="space-y-1.5">
                  <label className="font-semibold text-muted-foreground">Log Date</label>
                  <Input
                    type="date"
                    value={regularizeForm.date}
                    onChange={(e) => setRegularizeForm((p) => ({ ...p, date: e.target.value }))}
                    disabled={submitting}
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <label className="font-semibold text-muted-foreground">Correction Check-In</label>
                    <Input
                      type="time"
                      value={regularizeForm.check_in}
                      onChange={(e) => setRegularizeForm((p) => ({ ...p, check_in: e.target.value }))}
                      disabled={submitting}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="font-semibold text-muted-foreground">Correction Check-Out</label>
                    <Input
                      type="time"
                      value={regularizeForm.check_out}
                      onChange={(e) => setRegularizeForm((p) => ({ ...p, check_out: e.target.value }))}
                      disabled={submitting}
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="font-semibold text-muted-foreground">Justification Reason *</label>
                  <textarea
                    value={regularizeForm.reason}
                    onChange={(e) => setRegularizeForm((p) => ({ ...p, reason: e.target.value }))}
                    rows={3}
                    className="w-full bg-background border border-input text-foreground rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-primary text-xs"
                    placeholder="Provide justification why clock register was missing..."
                    disabled={submitting}
                    required
                  />
                </div>

                <div className="flex gap-2 justify-end pt-3 border-t">
                  <Button type="button" variant="outline" onClick={() => setShowRegModal(false)} disabled={submitting}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={submitting}>
                    {submitting && <Loader2 className="h-4 w-4 animate-spin mr-1.5" />}
                    Submit Application
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

export default AttendancePage;
