# attendance/views.py
# ── REPLACEMENT FILE ──
# Replace: Backend/lap/attendance/views.py
# Changes:
#  1. HolidayDetailView added  (PUT / PATCH / DELETE on individual holiday)
#  2. MyAttendanceView — holiday days injected into records list with
#     status='holiday'; summary.present includes holiday count
#  3. All datetime.now() → timezone.localtime(timezone.now()) for tz-awareness
from datetime import date, datetime, time, timedelta
from decimal import Decimal
import calendar as cal_mod

from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.shortcuts import get_object_or_404

from utils.permissions import make_permission, IsAuthenticatedUser
from accounts.tenant_utils import get_tenant_id
from accounts.models import User
from .models import AttendanceRecord, AttendanceRegularization, Holiday, OfficeLocation
from .serializers import (
    AttendanceRecordSerializer,
    RegularizationSerializer,
    HolidaySerializer,
    OfficeLocationSerializer,
)
from .settings_helper import (
    get_shift_start,
    get_shift_end,
    get_night_shift_enabled,
    get_night_shift_start,
    get_night_shift_end,
    get_active_shift_for_time,
    get_grace_minutes,
    get_standard_hours,
    get_half_day_hours,
    get_weekend_days,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now_local():
    return timezone.localtime(timezone.now())

def _today_local() -> date:
    return _now_local().date()

def _now_time_local() -> time:
    return _now_local().time().replace(tzinfo=None)


def _record_tenant_id(record):
    return (
        getattr(record, 'tenant_id', None)
        or getattr(getattr(record, 'employee', None), 'tenant_id', None)
        or 'default'
    )


def _snapshot_shift_policy(record, check_in_time=None):
    tenant_id = _record_tenant_id(record)
    active_shift = get_active_shift_for_time(check_in_time or record.check_in or _now_time_local(), tenant_id)
    record.shift_type = active_shift['type']
    record.shift_start_snapshot = active_shift['start']
    record.shift_end_snapshot = active_shift['end']
    record.grace_minutes_snapshot = get_grace_minutes(tenant_id)
    record.standard_hours_snapshot = Decimal(str(get_standard_hours(tenant_id)))
    record.half_day_hours_snapshot = Decimal(str(get_half_day_hours(tenant_id)))
    record.is_overnight_shift = active_shift['is_overnight']


def _snapshot_shift_policy_for_type(record, shift_type=None):
    tenant_id = _record_tenant_id(record)
    shift_type = shift_type or getattr(record, 'shift_type', 'day') or 'day'
    if shift_type == 'night' and get_night_shift_enabled(tenant_id):
        shift_start = get_night_shift_start(tenant_id)
        shift_end = get_night_shift_end(tenant_id)
        record.shift_type = 'night'
    else:
        shift_start = get_shift_start(tenant_id)
        shift_end = get_shift_end(tenant_id)
        record.shift_type = 'day'
    record.shift_start_snapshot = shift_start
    record.shift_end_snapshot = shift_end
    record.grace_minutes_snapshot = get_grace_minutes(tenant_id)
    record.standard_hours_snapshot = Decimal(str(get_standard_hours(tenant_id)))
    record.half_day_hours_snapshot = Decimal(str(get_half_day_hours(tenant_id)))
    record.is_overnight_shift = shift_end <= shift_start


def _refresh_record_from_current_policy(record):
    if not record or record.is_locked:
        return record
    if record.check_in:
        _snapshot_shift_policy(record, record.check_in)
    else:
        _snapshot_shift_policy_for_type(record, record.shift_type)
    if record.check_in and not record.check_in_at:
        record.check_in_at, record.check_out_at = _infer_attendance_datetimes(record)
    elif record.check_in and record.check_out and not record.check_out_at:
        _, record.check_out_at = _infer_attendance_datetimes(record)
    if record.check_in and record.check_out:
        record.hours_worked = Decimal(str(record.calculate_hours()))
        record.ot_hours = _calculate_ot_hours(record.check_in, record.check_out, record)
        record.status = _get_status(record.check_in, record.check_out, record.hours_worked, record)
    return record


def _attendance_date_for_shift(user, now_dt, active_shift):
    now_date = now_dt.date()
    now_time = now_dt.time().replace(tzinfo=None)
    if (
        active_shift['type'] == 'night'
        and active_shift['is_overnight']
        and now_time >= active_shift['start']
    ):
        day_shift_completed = AttendanceRecord.objects.filter(
            employee=user,
            date=now_date,
            shift_type='day',
            check_in__isnull=False,
            check_out__isnull=False,
        ).exists()
        if day_shift_completed:
            return now_date + timedelta(days=1)
    return now_date


def _combine_local(day, clock):
    value = datetime.combine(day, clock)
    return timezone.make_aware(value, timezone.get_current_timezone())


def _shift_window_for_record(record):
    tenant_id = _record_tenant_id(record)
    shift_start = getattr(record, 'shift_start_snapshot', None) or get_shift_start(tenant_id)
    shift_end = getattr(record, 'shift_end_snapshot', None) or get_shift_end(tenant_id)
    is_overnight = bool(
        getattr(record, 'is_overnight_shift', False)
        or shift_end <= shift_start
    )

    start_date = record.date
    if is_overnight and record.check_in_at and record.check_in_at.date() < record.date:
        start_date = record.date - timedelta(days=1)

    start = _combine_local(start_date, shift_start)
    end = _combine_local(start_date, shift_end)
    if is_overnight or end <= start:
        end += timedelta(days=1)
    return start, end


def _infer_attendance_datetimes(record):
    if not record.check_in:
        return None, None
    tenant_id = _record_tenant_id(record)
    shift_start = getattr(record, 'shift_start_snapshot', None) or get_shift_start(tenant_id)
    shift_end = getattr(record, 'shift_end_snapshot', None) or get_shift_end(tenant_id)
    is_overnight = bool(
        getattr(record, 'is_overnight_shift', False)
        or shift_end <= shift_start
    )
    check_in_date = record.date
    if is_overnight and record.check_in < shift_end:
        check_in_date = record.date - timedelta(days=1)
    elif is_overnight and getattr(record, 'shift_type', '') == 'night':
        previous_day_completed = AttendanceRecord.objects.filter(
            employee=record.employee,
            date=record.date - timedelta(days=1),
            shift_type='day',
            check_in__isnull=False,
            check_out__isnull=False,
        ).exists()
        if previous_day_completed:
            check_in_date = record.date - timedelta(days=1)

    ci = record.check_in_at or _combine_local(check_in_date, record.check_in)
    co = None
    if record.check_out:
        check_out_date = check_in_date
        if is_overnight and record.check_out <= shift_start:
            check_out_date = check_in_date + timedelta(days=1)
        co = record.check_out_at or _combine_local(check_out_date, record.check_out)
        if co <= ci:
            co += timedelta(days=1)
    return ci, co


def _get_status(check_in, check_out, hours_worked, record=None):
    if not check_in:
        return 'absent'
    if not check_out:
        return 'pending'

    tenant_id = _record_tenant_id(record) if record else None
    shift_start    = getattr(record, 'shift_start_snapshot', None) or get_shift_start(tenant_id)
    grace_minutes  = getattr(record, 'grace_minutes_snapshot', None) or get_grace_minutes(tenant_id)
    half_day_hours = getattr(record, 'half_day_hours_snapshot', None) or Decimal(str(get_half_day_hours(tenant_id)))

    if record and record.check_in_at:
        shift_start_at, _ = _shift_window_for_record(record)
        grace_cutoff = shift_start_at + timedelta(minutes=grace_minutes)
        ci = record.check_in_at
    else:
        ref_date     = date(2000, 1, 1)
        grace_cutoff = datetime.combine(ref_date, shift_start) + timedelta(minutes=grace_minutes)
        ci           = datetime.combine(ref_date, check_in)

    if hours_worked < half_day_hours:
        return 'half_day'
    if ci > grace_cutoff:
        return 'late'
    return 'present'


def _calculate_ot_hours(check_in, check_out, record=None):
    if not check_in or not check_out:
        return Decimal('0')

    tenant_id = _record_tenant_id(record) if record else None
    shift_end = getattr(record, 'shift_end_snapshot', None) or get_shift_end(tenant_id)
    shift_start = getattr(record, 'shift_start_snapshot', None) or get_shift_start(tenant_id)
    grace_minutes = getattr(record, 'grace_minutes_snapshot', None) or get_grace_minutes(tenant_id)
    if record and record.check_in_at and record.check_out_at:
        ci = record.check_in_at
        co = record.check_out_at
        start, end = _shift_window_for_record(record)
    else:
        ref_date = date(2000, 1, 1)
        ci = datetime.combine(ref_date, check_in)
        co = datetime.combine(ref_date, check_out)
        start = datetime.combine(ref_date, shift_start)
        end = datetime.combine(ref_date, shift_end)
        if co <= ci:
            co += timedelta(days=1)
        if end <= start:
            end += timedelta(days=1)
    grace_cutoff = start + timedelta(minutes=grace_minutes)
    late_minutes = max((ci - grace_cutoff).total_seconds() / 60, 0)
    ot_start = end + timedelta(minutes=late_minutes)

    if co <= ot_start:
        return Decimal('0')

    hours = (co - ot_start).total_seconds() / 3600
    return Decimal(str(round(hours, 2)))


def _setting_value(tenant_id, key):
    try:
        from notifications.models import SystemSetting
        setting = (
            SystemSetting.objects.filter(tenant_id=str(tenant_id or 'default'), key=key).first()
            or SystemSetting.objects.filter(tenant_id='default', key=key).first()
        )
        if setting:
            return setting.get_value()
    except Exception:
        return None
    return None


def _office_from_settings(tenant_id):
    latitude = _setting_value(tenant_id, 'office_latitude')
    longitude = _setting_value(tenant_id, 'office_longitude')
    if latitude in (None, '') or longitude in (None, ''):
        return None
    radius_meters = _setting_value(tenant_id, 'office_radius_meters') or 300
    try:
        return OfficeLocation(
            tenant_id=str(tenant_id or 'default'),
            name='Head Office',
            latitude=latitude,
            longitude=longitude,
            radius_meters=int(float(radius_meters)),
            is_active=True,
        )
    except (TypeError, ValueError):
        return None


def _active_office_for_request(request):
    tenant_id = get_tenant_id(request)
    return OfficeLocation.active_for_tenant(tenant_id) or _office_from_settings(tenant_id)


def _validate_location(lat, lon, request):
    office = _active_office_for_request(request)
    if office is None:
        return True, None, None, None
    if lat is None or lon is None:
        return False, None, office, 'Location is required for check-in/check-out. Please allow location access.'
    try:
        distance_m = office.distance_from(float(lat), float(lon))
    except (ValueError, TypeError):
        return False, None, office, 'Invalid location data sent.'
    if distance_m > office.radius_meters:
        return (
            False, round(distance_m, 1), office,
            f'You are {round(distance_m, 0):.0f} m away from the office. '
            f'Check-in is only allowed within {office.radius_meters} m.',
        )
    return True, round(distance_m, 1), office, None


def _user_work_mode(user):
    try:
        return user.profile.work_mode or 'office'
    except Exception:
        return 'office'


# ── OFFICE LOCATION ────────────────────────────────────────────────────────────

class OfficeLocationView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticatedUser()]
        return [make_permission('manage_settings')()]

    def get(self, request):
        office = _active_office_for_request(request)
        if not office:
            return Response({
                'id': None,
                'name': '',
                'latitude': None,
                'longitude': None,
                'radius_meters': 300,
                'is_active': False,
                'updated_at': None,
                'configured': False,
                'detail': 'No office location configured.',
            })
        data = OfficeLocationSerializer(office).data
        data['configured'] = True
        if not office.pk:
            data['id'] = None
            data['updated_at'] = None
        return Response(data)

    def post(self, request):
        name          = request.data.get('name', 'Head Office')
        latitude      = request.data.get('latitude')
        longitude     = request.data.get('longitude')
        radius_meters = request.data.get('radius_meters', 300)
        if latitude is None or longitude is None:
            return Response({'error': 'latitude and longitude are required'}, status=status.HTTP_400_BAD_REQUEST)
        OfficeLocation.objects.filter(
            tenant_id=get_tenant_id(request),
            is_active=True,
        ).update(is_active=False)
        office = OfficeLocation.objects.create(
            tenant_id=get_tenant_id(request),
            name=name, latitude=latitude, longitude=longitude,
            radius_meters=radius_meters, is_active=True,
        )
        try:
            from notifications.models import SystemSetting
            tenant_id = get_tenant_id(request)
            settings_payload = {
                'office_latitude': ('Office latitude', str(office.latitude), 'decimal'),
                'office_longitude': ('Office longitude', str(office.longitude), 'decimal'),
                'office_radius_meters': ('Office radius meters', str(office.radius_meters), 'integer'),
            }
            for key, (label, value, value_type) in settings_payload.items():
                SystemSetting.objects.update_or_create(
                    tenant_id=tenant_id,
                    key=key,
                    defaults={
                        'value': value,
                        'value_type': value_type,
                        'label': label,
                        'category': 'attendance',
                        'updated_by': request.user,
                    },
                )
        except Exception:
            pass
        return Response(OfficeLocationSerializer(office).data, status=status.HTTP_201_CREATED)


# ── CHECK-IN ──────────────────────────────────────────────────────────────────

class CheckInView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def post(self, request):
        work_mode = _user_work_mode(request.user)
        is_wfh   = work_mode == 'work_from_home'
        now_dt   = _now_local()
        now_time = now_dt.time().replace(tzinfo=None)
        active_shift = get_active_shift_for_time(now_time, get_tenant_id(request))
        attendance_date = _attendance_date_for_shift(request.user, now_dt, active_shift)
        shift_type = active_shift['type']

        if not is_wfh:
            lat = request.data.get('latitude')
            lon = request.data.get('longitude')
            ok, distance_m, office, error_msg = _validate_location(lat, lon, request)
            if not ok:
                return Response(
                    {'error': error_msg, 'distance_m': distance_m, 'allowed_radius': office.radius_meters if office else None},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            lat = request.data.get('latitude')
            lon = request.data.get('longitude')
            distance_m = None

        existing = AttendanceRecord.objects.filter(
            employee=request.user,
            date=attendance_date,
            shift_type=shift_type,
        ).first()

        if existing:
            existing.check_in = now_time
            existing.check_in_at = now_dt
            existing.check_out = None
            existing.check_out_at = None
            existing.hours_worked = Decimal('0')
            existing.ot_hours = Decimal('0')
            existing.status = 'present'
            existing.is_wfh   = is_wfh
            _snapshot_shift_policy(existing, now_time)
            if lat is not None:
                existing.checkin_latitude   = lat
                existing.checkin_longitude  = lon
                existing.checkin_distance_m = distance_m
            existing.save()
            record = existing
        else:
            record = AttendanceRecord(
                employee=request.user, date=attendance_date, shift_type=shift_type, check_in=now_time,
                check_in_at=now_dt,
                is_wfh=is_wfh, status='present',
                checkin_latitude=lat, checkin_longitude=lon, checkin_distance_m=distance_m,
            )
            _snapshot_shift_policy(record, now_time)
            record.save()
        return Response(AttendanceRecordSerializer(record).data, status=status.HTTP_200_OK)


# ── CHECK-OUT ─────────────────────────────────────────────────────────────────

class CheckOutView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def post(self, request):
        today    = _today_local()
        now_dt   = _now_local()
        now_time = now_dt.time().replace(tzinfo=None)
        lat = request.data.get('latitude')
        lon = request.data.get('longitude')

        record = AttendanceRecord.objects.filter(
            employee=request.user,
            check_in__isnull=False,
            check_out__isnull=True,
            date__lte=today,
        ).order_by('-date', '-created_at').first()
        if not record or not record.check_in:
            return Response({'error': 'No open check-in found'}, status=status.HTTP_400_BAD_REQUEST)
        if record.check_out:
            return Response({'error': 'Already checked out today'}, status=status.HTTP_400_BAD_REQUEST)

        if not record.is_wfh:
            ok, distance_m, office, error_msg = _validate_location(lat, lon, request)
            if not ok:
                return Response(
                    {'error': error_msg, 'distance_m': distance_m, 'allowed_radius': office.radius_meters if office else None},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            distance_m = None

        record.check_out    = now_time
        record.check_out_at = now_dt
        if not record.check_in_at:
            record.check_in_at, _ = _infer_attendance_datetimes(record)
        record.hours_worked = Decimal(str(record.calculate_hours()))

        record.ot_hours = _calculate_ot_hours(record.check_in, record.check_out, record)

        if lat is not None and not record.is_wfh:
            record.checkout_latitude   = lat
            record.checkout_longitude  = lon
            record.checkout_distance_m = distance_m
        elif lat is not None and record.is_wfh:
            record.checkout_latitude   = lat
            record.checkout_longitude  = lon
            record.checkout_distance_m = None

        record.status = _get_status(record.check_in, record.check_out, record.hours_worked, record)
        record.save()
        return Response(AttendanceRecordSerializer(record).data)


# ── TODAY ATTENDANCE ──────────────────────────────────────────────────────────

class TodayAttendanceView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        today   = _today_local()
        open_record = AttendanceRecord.objects.filter(
            employee=request.user,
            check_in__isnull=False,
            check_out__isnull=True,
            date__lte=today,
        ).order_by('-date', '-created_at').first()
        record = open_record or AttendanceRecord.objects.filter(
            employee=request.user,
            date=today,
        ).order_by('-shift_type', '-created_at').first()
        holiday = Holiday.objects.filter(tenant_id=get_tenant_id(request), date=today).first()
        return Response({
            'record':  AttendanceRecordSerializer(record).data if record else None,
            'is_wfh':  record.is_wfh if record else False,
            'work_mode': _user_work_mode(request.user),
            'holiday': {'date': str(holiday.date), 'name': holiday.name} if holiday else None,
            'date':    str(today),
        })


# ── MY ATTENDANCE (monthly view) ──────────────────────────────────────────────

class MyAttendanceView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        today = _today_local()
        month = int(request.query_params.get('month', today.month))
        year  = int(request.query_params.get('year',  today.year))

        records = AttendanceRecord.objects.filter(
            employee=request.user, date__year=year, date__month=month,
        ).order_by('date')

        for record in records:
            original = (
                record.shift_start_snapshot,
                record.shift_end_snapshot,
                record.grace_minutes_snapshot,
                record.standard_hours_snapshot,
                record.half_day_hours_snapshot,
                record.is_overnight_shift,
                record.check_in_at,
                record.check_out_at,
                record.hours_worked,
                record.ot_hours,
                record.status,
            )
            _refresh_record_from_current_policy(record)
            updated = (
                record.shift_start_snapshot,
                record.shift_end_snapshot,
                record.grace_minutes_snapshot,
                record.standard_hours_snapshot,
                record.half_day_hours_snapshot,
                record.is_overnight_shift,
                record.check_in_at,
                record.check_out_at,
                record.hours_worked,
                record.ot_hours,
                record.status,
            )
            if updated != original:
                record.save(update_fields=[
                    'shift_start_snapshot',
                    'shift_end_snapshot',
                    'grace_minutes_snapshot',
                    'standard_hours_snapshot',
                    'half_day_hours_snapshot',
                    'is_overnight_shift',
                    'check_in_at',
                    'check_out_at',
                    'hours_worked',
                    'ot_hours',
                    'status',
                ])

        from leave.models import LeaveRequest
        approved_leaves = LeaveRequest.objects.filter(
            employee=request.user, status='approved',
            start_date__lte=date(year, month, cal_mod.monthrange(year, month)[1]),
            end_date__gte=date(year, month, 1),
        ).select_related('leave_type')

        leave_dates = {}
        for lr in approved_leaves:
            is_lop = (not lr.leave_type.is_paid) or (lr.leave_type.code == 'LOP')
            cur = lr.start_date
            while cur <= lr.end_date:
                if cur.year == year and cur.month == month:
                    leave_dates[str(cur)] = {'name': lr.leave_type.name, 'is_lop': is_lop}
                cur += timedelta(days=1)

        holidays = list(Holiday.objects.filter(date__year=year, date__month=month).values('date', 'name'))
        holiday_date_set = {str(h['date']) for h in holidays}

        record_map = {}
        for r in records:
            record_map.setdefault(str(r.date), []).append(r)
        existing_dates = set(record_map.keys())
        serialized     = list(AttendanceRecordSerializer(records, many=True).data)

        today_str = str(today)

        # Missing checkout is not final until corrected/approved.
        for rec in serialized:
            source_records = record_map.get(rec.get('date'), [])
            open_shift_still_running = False
            for source_record in source_records:
                expected_end = source_record.expected_shift_end_at()
                if expected_end and _now_local() <= expected_end:
                    open_shift_still_running = True
                    break
            if (
                rec.get('check_in')
                and not rec.get('check_out')
                and rec.get('date') != today_str
                and not open_shift_still_running
            ):
                rec['status'] = 'pending'
                rec['pending_reason'] = 'missing_checkout'

        from attendance.settings_helper import is_weekend as _is_weekend
        month_end = date(year, month, cal_mod.monthrange(year, month)[1])
        visible_until = min(today - timedelta(days=1), month_end)
        cur = date(year, month, 1)
        while cur <= visible_until:
            cur_str = str(cur)
            if (
                not _is_weekend(cur)
                and cur_str not in existing_dates
                and cur_str not in holiday_date_set
                and cur_str not in leave_dates
            ):
                serialized.append({
                    'id': None, 'date': cur_str,
                    'check_in': None, 'check_out': None,
                    'hours_worked': 0, 'ot_hours': 0,
                    'status': 'pending', 'is_wfh': False,
                    'leave_name': None, 'is_lop': False,
                    'pending_reason': 'missing_attendance',
                })
            cur += timedelta(days=1)

        # ── Inject holiday virtual records ────────────────────────────────────
        # If there is no attendance record on a holiday → create a virtual entry
        # with status='holiday' so the calendar shows it correctly.
        # If there IS a record on that day → tag it with holiday_name.
        for h in holidays:
            h_str = str(h['date'])
            if h_str not in existing_dates:
                serialized.append({
                    'id': None, 'date': h_str,
                    'check_in': None, 'check_out': None,
                    'hours_worked': 0, 'ot_hours': 0,
                    'status': 'holiday', 'is_wfh': False,
                    'leave_name': None, 'is_lop': False,
                    'holiday_name': h['name'],
                })
            else:
                for rec in serialized:
                    if rec.get('date') == h_str:
                        rec['holiday_name'] = h['name']
                        # Keep original status (present/late etc.) but flag holiday
                        if rec.get('status') in ('absent',):
                            rec['status'] = 'holiday'
                        break

        # ── Inject approved leave records ─────────────────────────────────────
        for date_str, leave_info in leave_dates.items():
            leave_status = 'lop_leave' if leave_info['is_lop'] else 'leave'
            if date_str not in existing_dates and date_str not in holiday_date_set:
                serialized.append({
                    'id': None, 'date': date_str,
                    'check_in': None, 'check_out': None,
                    'hours_worked': 0, 'ot_hours': 0,
                    'status': leave_status, 'is_wfh': False,
                    'leave_name': leave_info['name'], 'is_lop': leave_info['is_lop'],
                })
            elif date_str not in holiday_date_set:
                for rec in serialized:
                    if rec.get('date') == date_str:
                        if rec.get('status') in ('absent', 'half_day', 'pending', 'leave', 'lop_leave'):
                            rec['status'] = leave_status
                        rec['leave_name'] = leave_info['name']
                        rec['is_lop']     = leave_info['is_lop']
                        break

        # ── Summary ───────────────────────────────────────────────────────────
        status_counts = {}
        grouped_serialized = {}
        for rec in serialized:
            grouped_serialized.setdefault(rec.get('date'), []).append(rec)

        for day_records in grouped_serialized.values():
            statuses = [r.get('status', 'absent') for r in day_records]
            if 'leave' in statuses:
                st = 'leave'
            elif 'lop_leave' in statuses:
                st = 'lop_leave'
            elif 'late' in statuses:
                st = 'late'
            elif 'present' in statuses:
                st = 'present'
            elif 'half_day' in statuses:
                st = 'half_day'
            elif 'holiday' in statuses:
                st = 'holiday'
            elif 'pending' in statuses:
                st = 'pending'
            else:
                st = statuses[0] if statuses else 'absent'
            status_counts[st] = status_counts.get(st, 0) + 1

        summary = {
            # present + late + holiday all count as "present" for display
            'present':   status_counts.get('present', 0) + status_counts.get('late', 0) + status_counts.get('holiday', 0) + status_counts.get('leave', 0),
            'absent':    status_counts.get('absent', 0),
            'pending':   status_counts.get('pending', 0),
            'late':      status_counts.get('late', 0),
            'half_day':  status_counts.get('half_day', 0),
            'leave':     status_counts.get('leave', 0),
            'lop_leave': status_counts.get('lop_leave', 0),
            'holiday':   status_counts.get('holiday', 0),
            'total_hours': float(sum(r.hours_worked for r in records if r.hours_worked)),
            'total_ot':    float(sum(r.ot_hours     for r in records if r.ot_hours)),
        }

        tenant_id = get_tenant_id(request)
        shift_start   = get_shift_start(tenant_id)
        grace_minutes = get_grace_minutes(tenant_id)
        late_cutoff   = (
            datetime.combine(today, shift_start) + timedelta(minutes=grace_minutes)
        ).strftime('%H:%M')

        return Response({
            'month':    month,
            'year':     year,
            'summary':  summary,
            'records':  serialized,
            'holidays': holidays,
            'policy': {
                'shift_start':   shift_start.strftime('%H:%M'),
                'shift_end':     get_shift_end(tenant_id).strftime('%H:%M'),
                'grace_minutes': grace_minutes,
                'late_cutoff':   late_cutoff,
                'standard_hours': get_standard_hours(tenant_id),
                'half_day_hours': get_half_day_hours(tenant_id),
                'weekend_days': get_weekend_days(),
                'night_shift_enabled': get_night_shift_enabled(tenant_id),
                'night_shift_start':   get_night_shift_start(tenant_id).strftime('%H:%M'),
                'night_shift_end':     get_night_shift_end(tenant_id).strftime('%H:%M'),
            },
        })


# ── ALL EMPLOYEES ATTENDANCE ──────────────────────────────────────────────────

class AllAttendanceView(APIView):
    permission_classes = [make_permission('view_team_attendance')]

    def get(self, request):
        today  = _today_local()
        month  = int(request.query_params.get('month', today.month))
        year   = int(request.query_params.get('year',  today.year))
        emp_id = request.query_params.get('employee')

        qs = AttendanceRecord.objects.filter(
            tenant_id=get_tenant_id(request),
            date__year=year, date__month=month,
        ).select_related('employee', 'employee__profile').order_by('employee__username', 'date')

        if emp_id:
            qs = qs.filter(employee_id=emp_id)
        return Response(AttendanceRecordSerializer(qs, many=True).data)


# ── APPLY REGULARISATION ──────────────────────────────────────────────────────

class ApplyRegularizationView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def post(self, request):
        attendance_id      = request.data.get('attendance_id')
        request_date       = request.data.get('date')
        reason             = request.data.get('reason', '')
        requested_checkin  = request.data.get('requested_checkin')
        requested_checkout = request.data.get('requested_checkout')
        shift_type         = request.data.get('shift_type', 'day')

        if attendance_id:
            try:
                record = AttendanceRecord.objects.get(id=attendance_id, employee=request.user)
            except AttendanceRecord.DoesNotExist:
                return Response({'error': 'Attendance record not found'}, status=status.HTTP_404_NOT_FOUND)
        elif request_date:
            try:
                parsed_date = date.fromisoformat(request_date)
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

            if shift_type == 'night':
                day_shift_completed = AttendanceRecord.objects.filter(
                    employee=request.user,
                    date=parsed_date,
                    shift_type='day',
                    check_in__isnull=False,
                    check_out__isnull=False,
                ).exists()
                if day_shift_completed:
                    parsed_date = parsed_date + timedelta(days=1)

            record, _ = AttendanceRecord.objects.get_or_create(
                employee=request.user,
                date=parsed_date,
                shift_type=shift_type,
                defaults={
                    'tenant_id': get_tenant_id(request),
                    'status': 'pending',
                    'note': 'Pending regularization request',
                },
            )
            if record.tenant_id != get_tenant_id(request):
                record.tenant_id = get_tenant_id(request)
                record.save(update_fields=['tenant_id'])
            if not record.shift_start_snapshot or not record.shift_end_snapshot:
                _snapshot_shift_policy_for_type(record, shift_type)
                record.save(update_fields=[
                    'shift_type',
                    'shift_start_snapshot',
                    'shift_end_snapshot',
                    'grace_minutes_snapshot',
                    'standard_hours_snapshot',
                    'half_day_hours_snapshot',
                    'is_overnight_shift',
                ])
        else:
            return Response({'error': 'attendance_id or date is required'}, status=status.HTTP_400_BAD_REQUEST)

        if hasattr(record, 'regularization'):
            reg = record.regularization
            if reg.status == 'rejected':
                reg.status = 'pending'
                reg.reason = reason
                reg.requested_checkin = requested_checkin
                reg.requested_checkout = requested_checkout
                reg.approved_by = None
                reg.approver_note = ''
                reg.save()
                return Response(RegularizationSerializer(reg).data, status=status.HTTP_200_OK)
            return Response({'error': 'Regularisation already submitted for this date'}, status=status.HTTP_400_BAD_REQUEST)

        reg = AttendanceRegularization.objects.create(
            attendance=record, employee=request.user,
            reason=reason,
            requested_checkin=requested_checkin, requested_checkout=requested_checkout,
        )
        return Response(RegularizationSerializer(reg).data, status=status.HTTP_201_CREATED)


# ── MY REGULARISATIONS ────────────────────────────────────────────────────────

class MyRegularizationsView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        regs = AttendanceRegularization.objects.filter(
            employee=request.user,
            tenant_id=get_tenant_id(request),
        ).order_by('-created_at')
        return Response(RegularizationSerializer(regs, many=True).data)


# ── ALL REGULARISATIONS ───────────────────────────────────────────────────────

class AllRegularizationsView(APIView):
    permission_classes = [make_permission('approve_regularize')]

    def get(self, request):
        status_filter = request.query_params.get('status')
        qs = AttendanceRegularization.objects.select_related(
            'employee', 'employee__profile', 'attendance',
        ).filter(tenant_id=get_tenant_id(request)).order_by('-created_at')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response(RegularizationSerializer(qs, many=True).data)


# ── APPROVE / REJECT REGULARISATION ──────────────────────────────────────────

class ApproveRegularizationView(APIView):
    permission_classes = [make_permission('approve_regularize')]

    def post(self, request, pk):
        reg    = get_object_or_404(
            AttendanceRegularization,
            pk=pk,
            tenant_id=get_tenant_id(request),
        )
        action = request.data.get('action')
        note   = request.data.get('note', '')

        if action not in ('approve', 'reject'):
            return Response({'error': "action must be 'approve' or 'reject'"}, status=status.HTTP_400_BAD_REQUEST)

        reg.status        = 'approved' if action == 'approve' else 'rejected'
        reg.approved_by   = request.user
        reg.approver_note = note

        if action == 'approve':
            record = reg.attendance
            if reg.requested_checkin:
                record.check_in  = reg.requested_checkin
            if reg.requested_checkout:
                record.check_out = reg.requested_checkout
            if not record.shift_start_snapshot or not record.shift_end_snapshot:
                _snapshot_shift_policy_for_type(record, record.shift_type)
            if record.check_in:
                inferred_check_in, inferred_check_out = _infer_attendance_datetimes(record)
                record.check_in_at = inferred_check_in
                record.check_out_at = inferred_check_out
            if record.check_in and record.check_out:
                record.hours_worked = Decimal(str(record.calculate_hours()))
                record.ot_hours = _calculate_ot_hours(record.check_in, record.check_out, record)
                record.status = _get_status(record.check_in, record.check_out, record.hours_worked, record)
            record.save()

        reg.save()
        carry_forward = None
        if action == 'approve':
            try:
                from payroll.engine import queue_locked_regularization_adjustment
                carry_forward = queue_locked_regularization_adjustment(reg)
            except Exception:
                carry_forward = None
        payload = {'message': f'Regularisation {reg.status}', 'data': RegularizationSerializer(reg).data}
        if carry_forward:
            payload['payroll_carry_forward'] = {
                'amount': float(carry_forward.amount),
                'source_month': carry_forward.source_month,
                'source_year': carry_forward.source_year,
                'status': carry_forward.status,
            }
        return Response(payload)


# ── HOLIDAYS — LIST / CREATE ──────────────────────────────────────────────────
# GET  /attendance/holidays/     — all authenticated users
# POST /attendance/holidays/     — manage_settings only

class HolidayListView(generics.ListCreateAPIView):
    serializer_class = HolidaySerializer

    def get_queryset(self):
        return Holiday.objects.filter(tenant_id=get_tenant_id(self.request))

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticatedUser()]
        return [make_permission('manage_settings')()]

    def perform_create(self, serializer):
        serializer.save(tenant_id=get_tenant_id(self.request))


# ── HOLIDAYS — EDIT / DELETE ──────────────────────────────────────────────────
# PUT   /attendance/holidays/<id>/
# PATCH /attendance/holidays/<id>/
# DELETE /attendance/holidays/<id>/

class HolidayDetailView(APIView):
    permission_classes = [make_permission('manage_settings')]

    def _get_holiday(self, pk):
        return get_object_or_404(Holiday, pk=pk, tenant_id=get_tenant_id(self.request))

    def put(self, request, pk):
        holiday    = self._get_holiday(pk)
        serializer = HolidaySerializer(holiday, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        holiday    = self._get_holiday(pk)
        serializer = HolidaySerializer(holiday, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        holiday = self._get_holiday(pk)
        name    = holiday.name
        holiday.delete()
        return Response({'message': f'Holiday "{name}" deleted successfully.'}, status=status.HTTP_200_OK)
