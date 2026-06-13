# notifications/management/commands/seed_system_settings.py
"""
Run: python manage.py seed_system_settings
Safe to re-run — uses get_or_create so existing values are preserved.
All payroll settings are dynamic. No hardcoded values anywhere.
"""
from django.core.management.base import BaseCommand
from notifications.models import SystemSetting


SETTINGS = [

    # ═══════════════ ATTENDANCE ═══════════════
    dict(
        key='work_days_per_week', value='5', value_type='integer', category='attendance',
        label='Work Days Per Week',
        description='5 = Mon–Fri (Sat & Sun off). 6 = Mon–Sat (Sun off only).',
    ),
    dict(
        key='weekend_days', value='["saturday","sunday"]', value_type='json', category='attendance',
        label='Weekend / Week-off Days',
        description='JSON list. ["saturday","sunday"] = 5-day week. ["sunday"] = 6-day week.',
    ),
    dict(
        key='work_start_time', value='09:00', value_type='time', category='attendance',
        label='Shift Start Time',
        description='Official shift start time (HH:MM). Used for late marking.',
    ),
    dict(
        key='work_end_time', value='18:00', value_type='time', category='attendance',
        label='Shift End Time',
        description='Official shift end time (HH:MM). Used for OT calculation.',
    ),
    dict(
        key='night_shift_enabled', value='false', value_type='boolean', category='attendance',
        label='Night Shift Enabled',
        description='If true, check-ins during the configured night window use night shift timings.',
    ),
    dict(
        key='night_shift_start_time', value='22:00', value_type='time', category='attendance',
        label='Night Shift Start Time',
        description='Official night shift start time (HH:MM). Example: 22:00.',
    ),
    dict(
        key='night_shift_end_time', value='06:00', value_type='time', category='attendance',
        label='Night Shift End Time',
        description='Official night shift end time (HH:MM). Next-day checkout is handled automatically.',
    ),
    dict(
        key='work_hours_per_day', value='8', value_type='integer', category='attendance',
        label='Work Hours Per Day',
        description='Standard working hours per day. Affects OT pay rate.',
    ),
    dict(
        key='grace_period_minutes', value='15', value_type='integer', category='attendance',
        label='Grace Period (Minutes)',
        description='Minutes after shift start before marking Late.',
    ),
    dict(
        key='half_day_hours', value='4', value_type='decimal', category='attendance',
        label='Half Day Threshold (Hours)',
        description='If hours worked < this value → Half Day Absent.',
    ),
    dict(
        key='late_marks_per_half_day', value='3', value_type='integer', category='attendance',
        label='Late Marks → Half-Day LOP',
        description='How many late arrivals trigger 0.5 LOP. Default 3: 3 lates = 0.5 LOP.',
    ),
    dict(
        key='overtime_multiplier', value='1.5', value_type='decimal', category='attendance',
        label='Overtime Pay Multiplier',
        description='OT pay = hourly rate × OT hours × this. Default 1.5 = time-and-a-half.',
    ),
    dict(
        key='auto_absent_enabled', value='true', value_type='boolean', category='attendance',
        label='Auto Absent Marking',
        description='If true, nightly cron marks employees absent if no check-in recorded.',
    ),
    dict(
        key='wfh_enabled', value='true', value_type='boolean', category='attendance',
        label='Work From Home (WFH) Enabled',
        description='If false, WFH option is hidden from employees in regularization.',
    ),
    dict(
        key='regularization_window_days', value='7', value_type='integer', category='attendance',
        label='Regularization Window (Days)',
        description='Employee can request attendance correction within this many past days.',
    ),

    # ═══════════════ LEAVE ═══════════════
    dict(
        key='leave_year_basis', value='calendar', value_type='string', category='leave',
        label='Leave Year Basis',
        description='calendar = Jan–Dec. fiscal = based on fiscal_year_start_month.',
    ),
    dict(
        key='carry_forward_month', value='1', value_type='integer', category='leave',
        label='Carry Forward Processing Month',
        description='Month (1–12) when EL carry-forward is applied. Default 1 = January.',
    ),
    dict(
        key='cl_days_per_year', value='12', value_type='integer', category='leave',
        label='Casual Leave (CL) — Days/Year',
        description='Annual CL allocation for Regular employees.',
    ),
    dict(
        key='cl_monthly_cap', value='2', value_type='integer', category='leave',
        label='Casual Leave — Monthly Cap',
        description='Max CL per month. 0 = no cap.',
    ),

    dict(
        key='sl_advance_notice_days', value='0', value_type='integer', category='leave',
        label='SL Advance Notice (Days)',
        description='Minimum working days notice required for Sick Leave. 0 = no restriction.',
    ),
    dict(
        key='el_advance_notice_days', value='1', value_type='integer', category='leave',
        label='EL Advance Notice (Days)',
        description='Minimum working days notice required for Earned Leave.',
    ),
    dict(
        key='sl_days_per_year', value='12', value_type='integer', category='leave',
        label='Sick Leave (SL) — Days/Year',
        description='Annual SL allocation for Regular employees.',
    ),
    dict(
        key='sl_doc_required_after_days', value='2', value_type='integer', category='leave',
        label='SL Medical Certificate After (Days)',
        description='Consecutive sick days after which medical certificate is mandatory.',
    ),
    dict(
        key='el_days_per_year', value='15', value_type='integer', category='leave',
        label='Earned Leave (EL) — Days/Year',
        description='Annual EL allocation for Regular employees.',
    ),
    dict(
        key='el_max_carry_forward', value='45', value_type='integer', category='leave',
        label='EL — Max Carry Forward (Days)',
        description='Maximum EL days that carry to next year. Excess is lapsed.',
    ),
    dict(
        key='el_carry_forward', value='true', value_type='boolean', category='leave',
        label='EL — Carry Forward Enabled',
        description='Whether unused Earned Leave balance carries to next year.',
    ),
    dict(
        key='cl_is_paid', value='true', value_type='boolean', category='leave',
        label='CL — Paid Leave',
        description='Whether Casual Leave is paid. Affects LOP deduction in payslip.',
    ),
    dict(
        key='sl_is_paid', value='true', value_type='boolean', category='leave',
        label='SL — Paid Leave',
        description='Whether Sick Leave is paid. Affects LOP deduction in payslip.',
    ),
    dict(
        key='el_is_paid', value='true', value_type='boolean', category='leave',
        label='EL — Paid Leave',
        description='Whether Earned Leave is paid. Affects LOP deduction in payslip.',
    ),
    dict(
        key='sandwich_rule_enabled', value='true', value_type='boolean', category='leave',
        label='Sandwich Rule',
        description='If true, weekends between leave days are counted as leave.',
    ),
    dict(
        key='probation_earned_leave', value='false', value_type='boolean', category='leave',
        label='Earned Leave During Probation',
        description='If false, probation employees are not eligible for EL.',
    ),
    dict(
        key='leave_encashment_enabled', value='true', value_type='boolean', category='leave',
        label='Leave Encashment Enabled',
        description='If true, EL encashment allowed at year-end.',
    ),
    dict(
        key='half_day_leave_enabled', value='true', value_type='boolean', category='leave',
        label='Half Day Leave Enabled',
        description='If true, employees can apply for half-day leave.',
    ),
    dict(
        key='leave_balance_low_threshold', value='2', value_type='integer', category='leave',
        label='Low Balance Alert (Days)',
        description='Show low balance warning when remaining days fall below this.',
    ),
    dict(
        key='maternity_leave_days', value='182', value_type='integer', category='leave',
        label='Maternity Leave (Days)',
        description='Maternity leave days for Regular employees.',
    ),
    dict(
        key='paternity_leave_days', value='7', value_type='integer', category='leave',
        label='Paternity Leave (Days)',
        description='Paternity leave days for Regular employees.',
    ),

    # ═══════════════ PAYROLL — ALL 11 DYNAMIC SETTINGS ═══════════════
    dict(
        key='basic_salary_percent', value='40', value_type='decimal', category='payroll',
        label='Basic Salary (% of CTC)',
        description='Basic = Annual CTC × this % ÷ 12. Used in salary config auto-fill. Change here → all new salary configs auto-fill with new value.',
    ),
    dict(
        key='hra_percent_metro', value='50', value_type='decimal', category='payroll',
        label='HRA % of Basic — Metro City',
        description='HRA for metro employees = Basic × this %. Change here → salary config auto-fills HRA % automatically.',
    ),
    dict(
        key='hra_percent_nonmetro', value='40', value_type='decimal', category='payroll',
        label='HRA % of Basic — Non-Metro',
        description='HRA for non-metro employees = Basic × this %.',
    ),
    dict(
        key='da_percent', value='10', value_type='decimal', category='payroll',
        label='DA % of Basic (Dearness Allowance)',
        description='DA = Basic × this %. Shown in salary config auto-fill. Change here → reflects in all new structures.',
    ),
    dict(
        key='pf_employee_percent', value='12', value_type='decimal', category='payroll',
        label='PF Employee Contribution (%)',
        description='Employee PF deduction = Basic × this %. Change here → instantly reflected in next payroll run and payslip.',
    ),
    dict(
        key='pf_employer_percent', value='12', value_type='decimal', category='payroll',
        label='PF Employer Contribution (%)',
        description='Employer PF contribution = Basic × this % (part of CTC). Shown in CTC breakdown.',
    ),
    dict(
        key='esi_threshold_salary', value='21000', value_type='integer', category='payroll',
        label='ESI Salary Threshold (₹)',
        description='If effective gross ≤ this amount, ESI is deducted. Above this = ESI exempt. Change here → applies to next payroll run automatically.',
    ),
    dict(
        key='esi_employee_percent', value='0.75', value_type='decimal', category='payroll',
        label='ESI Employee Contribution (%)',
        description='Employee ESI deduction = gross × this %. Change here → reflected in payroll run and payslip immediately.',
    ),
    dict(
        key='esi_employer_percent', value='3.25', value_type='decimal', category='payroll',
        label='ESI Employer Contribution (%)',
        description='Employer ESI contribution = gross × this % (part of CTC). Shown in CTC breakup.',
    ),
    dict(
        key='payroll_lock_day', value='1', value_type='integer', category='payroll',
        label='Payroll Lock Day (1–31)',
        description='Fixed at day 1. Payroll for a completed month can be approved and locked from the 1st of the next month.',
    ),
    dict(
        key='tds_flat_percent_contract', value='10', value_type='decimal', category='payroll',
        label='TDS Flat Rate — Contract Employees (%)',
        description='Flat TDS % applied to contract employee gross. Regular employees use income slab TDS. Change here → next run uses new rate.',
    ),
    dict(
        key='pt_flat_amount',
        value='200',
        value_type='integer', category='payroll',
        label='Professional Tax (₹/month)',
        description='Flat PT amount deducted per month. Enter 200 → deducts ₹200. Enter 100 → deducts ₹100. Enter 0 → no PT. Prorated by attendance days.',
    ),

    # ═══════════════ GENERAL ═══════════════
    dict(
        key='pt_threshold_salary', value='15000', value_type='integer', category='payroll',
        label='Professional Tax Gross Threshold',
        description='Monthly gross threshold for PT. Gross below/equal this uses below-threshold PT; above this uses above-threshold PT.',
    ),
    dict(
        key='pt_below_threshold_amount', value='0', value_type='integer', category='payroll',
        label='Professional Tax Below Threshold',
        description='PT deducted when monthly gross salary is below/equal to the PT threshold.',
    ),
    dict(
        key='pt_above_threshold_amount', value='200', value_type='integer', category='payroll',
        label='Professional Tax Above Threshold',
        description='PT deducted when monthly gross salary is above the PT threshold. Prorated by attendance days in payroll.',
    ),
    dict(
        key='company_name', value='My Company', value_type='string', category='general',
        label='Company Name',
        description='Shown in payslip header, emails, and reports.',
    ),
    dict(
        key='company_logo_url', value='', value_type='string', category='general',
        label='Company Logo URL',
        description='Logo URL shown in payslip and email headers.',
    ),
    dict(
        key='fiscal_year_start_month', value='4', value_type='integer', category='general',
        label='Fiscal Year Start Month',
        description='1 = January, 4 = April.',
    ),
    dict(
        key='probation_period_months', value='6', value_type='integer', category='general',
        label='Probation Period (Months)',
        description='Employees on probation for first N months from joining.',
    ),
    dict(
        key='timezone', value='Asia/Kolkata', value_type='string', category='general',
        label='Timezone',
        description='Company timezone for attendance timestamps.',
    ),
    dict(
        key='office_latitude', value='', value_type='decimal', category='general',
        label='Office Latitude',
        description='Latitude used for office check-in/check-out location validation.',
    ),
    dict(
        key='office_longitude', value='', value_type='decimal', category='general',
        label='Office Longitude',
        description='Longitude used for office check-in/check-out location validation.',
    ),
    dict(
        key='office_radius_meters', value='300', value_type='integer', category='general',
        label='Office Radius (Meters)',
        description='Allowed distance from office for check-in/check-out. Default is 300 meters.',
    ),
    dict(
        key='currency', value='INR', value_type='string', category='general',
        label='Currency',
        description='Currency symbol used in payroll and reports.',
    ),
]


class Command(BaseCommand):
    help = 'Seed all system settings (safe to re-run)'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        seen_keys = set()

        for s in SETTINGS:
            key = s['key']
            if key in seen_keys:
                self.stdout.write(self.style.WARNING(f'  Skipping duplicate in seed: {key}'))
                continue
            seen_keys.add(key)

            obj, was_created = SystemSetting.objects.get_or_create(
                key=key,
                defaults={
                    'value':       s['value'],
                    'value_type':  s['value_type'],
                    'label':       s['label'],
                    'category':    s['category'],
                    'description': s['description'],
                },
            )

            # Always update label and description to latest
            if not was_created:
                obj.label       = s['label']
                obj.description = s['description']
                obj.category    = s['category']
                obj.save(update_fields=['label', 'description', 'category'])
                updated += 1
            else:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done: {created} created, {updated} updated ({len(seen_keys)} total settings).'
        ))
