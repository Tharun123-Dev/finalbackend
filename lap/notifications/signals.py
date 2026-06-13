def create_notif(user, title, body, ntype='general'):
    try:
        from notifications.models import Notification
        Notification.objects.create(user=user, title=title, body=body, type=ntype)
    except Exception as e:
        print(f"[NOTIF ERROR] create_notif: {e}")


def get_name(user):
    return user.get_full_name().strip() or user.username


# ─────────────────────────────────────────────
#  LEAVE
# ─────────────────────────────────────────────
def on_leave_request(sender, instance, created, **kwargs):
    try:
        from accounts.models import User
        from employees.models import EmployeeProfile

        emp_name = get_name(instance.employee)
        lt_name  = instance.leave_type.name
        s_date   = instance.start_date
        e_date   = instance.end_date
        days     = instance.days

        if created:
            # 1. Notify applicant
            create_notif(instance.employee,
                'Leave Application Submitted 📋',
                f'Your {lt_name} from {s_date} to {e_date} ({days} day(s)) has been submitted.',
                'leave_applied')

            # 2. Notify manager
            try:
                profile = EmployeeProfile.objects.get(user=instance.employee)
                if profile.manager:
                    create_notif(profile.manager,
                        f'New Leave Request — {emp_name}',
                        f'{emp_name} applied for {lt_name} from {s_date} to {e_date} ({days} day(s)). Please review.',
                        'leave_applied')
            except Exception as e:
                print(f"[NOTIF leave manager] {e}")

            # 3. Notify HR
            for hr in User.objects.filter(role='hr', is_active=True):
                create_notif(hr,
                    f'Leave Request Pending — {emp_name}',
                    f'{emp_name} applied for {lt_name} ({days} day(s)) from {s_date} to {e_date}.',
                    'leave_applied')

            # 4. Notify Admin
            for admin in User.objects.filter(role='admin', is_active=True):
                create_notif(admin,
                    f'Leave Request — {emp_name}',
                    f'{emp_name} applied for {lt_name} from {s_date} to {e_date} ({days} day(s)).',
                    'leave_applied')

        else:
            # Status changed
            if instance.status == 'approved':
                approver = get_name(instance.approved_by) if instance.approved_by else 'Manager'
                create_notif(instance.employee,
                    'Leave Approved ✅',
                    f'Your {lt_name} from {s_date} to {e_date} has been approved by {approver}.',
                    'leave_approved')

            elif instance.status == 'rejected':
                reason = instance.approver_note or 'No reason provided'
                create_notif(instance.employee,
                    'Leave Rejected ❌',
                    f'Your {lt_name} from {s_date} to {e_date} was rejected. Reason: {reason}',
                    'leave_rejected')

            elif instance.status == 'cancelled':
                create_notif(instance.employee,
                    'Leave Cancelled 🚫',
                    f'Your {lt_name} request from {s_date} to {e_date} has been cancelled.',
                    'leave_cancelled')

    except Exception as e:
        print(f"[NOTIF on_leave_request] {e}")


# ─────────────────────────────────────────────
#  ATTENDANCE — check-in / check-out / absent
# ─────────────────────────────────────────────
def on_attendance_record(sender, instance, created, **kwargs):
    try:
        from accounts.models import User
        from employees.models import EmployeeProfile

        emp_name = get_name(instance.employee)

        if created:
            if instance.status == 'absent':
                # Notify employee
                create_notif(instance.employee,
                    'Marked Absent 🔴',
                    f'You have been marked absent on {instance.date}. Submit a regularization request if this is incorrect.',
                    'attendance_absent')

                # Notify manager
                try:
                    profile = EmployeeProfile.objects.get(user=instance.employee)
                    if profile.manager:
                        create_notif(profile.manager,
                            f'{emp_name} Absent Today',
                            f'{emp_name} was marked absent on {instance.date}.',
                            'attendance_absent')
                except Exception as e:
                    print(f"[NOTIF absent manager] {e}")

            elif instance.status == 'late':
                create_notif(instance.employee,
                    'Late Arrival Marked ⏰',
                    f'You were marked late on {instance.date}. Check-in: {instance.check_in}.',
                    'attendance_absent')

            elif instance.is_wfh:
                create_notif(instance.employee,
                    'WFH Logged 🏠',
                    f'Your Work From Home for {instance.date} has been recorded.',
                    'general')

        else:
            # Existing record updated
            if instance.check_in and not instance.check_out:
                create_notif(instance.employee,
                    'Check-in Recorded ✅',
                    f'Your check-in for {instance.date} at {instance.check_in} has been recorded.',
                    'general')
            elif instance.check_out:
                hrs = instance.hours_worked
                ot  = instance.ot_hours
                msg = f'Check-out recorded at {instance.check_out}. Hours worked: {hrs}h.'
                if ot and float(ot) > 0:
                    msg += f' Overtime: {ot}h.'
                create_notif(instance.employee,
                    'Check-out Recorded 🕐',
                    msg,
                    'general')

    except Exception as e:
        print(f"[NOTIF on_attendance_record] {e}")


# ─────────────────────────────────────────────
#  ATTENDANCE REGULARIZATION
# ─────────────────────────────────────────────
def on_regularization(sender, instance, created, **kwargs):
    try:
        from accounts.models import User
        from employees.models import EmployeeProfile

        emp_name   = get_name(instance.employee)
        att_date   = instance.attendance.date

        if created:
            create_notif(instance.employee,
                'Regularization Request Submitted 🔄',
                f'Your attendance regularization request for {att_date} has been submitted. Awaiting approval.',
                'regularization')

            # Notify manager
            try:
                profile = EmployeeProfile.objects.get(user=instance.employee)
                if profile.manager:
                    create_notif(profile.manager,
                        f'Regularization Request — {emp_name}',
                        f'{emp_name} submitted an attendance correction for {att_date}. Reason: {instance.reason}',
                        'regularization')
            except Exception as e:
                print(f"[NOTIF regularization manager] {e}")

            # Notify HR
            for hr in User.objects.filter(role='hr', is_active=True):
                create_notif(hr,
                    f'Regularization — {emp_name}',
                    f'{emp_name} needs attendance correction for {att_date}.',
                    'regularization')

        else:
            if instance.status == 'approved':
                create_notif(instance.employee,
                    'Regularization Approved ✅',
                    f'Your attendance correction for {att_date} has been approved.',
                    'regularization')

            elif instance.status == 'rejected':
                note = instance.approver_note or 'No reason given'
                create_notif(instance.employee,
                    'Regularization Rejected ❌',
                    f'Your attendance correction for {att_date} was rejected. Note: {note}',
                    'regularization')

    except Exception as e:
        print(f"[NOTIF on_regularization] {e}")


# ─────────────────────────────────────────────
#  PAYROLL RUN — status changes
# ─────────────────────────────────────────────
def on_payroll_run(sender, instance, created, **kwargs):
    try:
        from accounts.models import User
        import calendar
        month_name = calendar.month_name[instance.month]

        if not created:
            if instance.status == 'processed':
                # Notify all admins + HR
                for u in User.objects.filter(role__in=['admin', 'hr'], is_active=True):
                    create_notif(u,
                        f'Payroll Processed — {month_name} {instance.year} ✅',
                        f'Payroll for {month_name} {instance.year} has been calculated. Please review and approve.',
                        'payroll_processed')

            elif instance.status == 'approved':
                # Notify all admins + HR
                for u in User.objects.filter(role__in=['admin', 'hr'], is_active=True):
                    create_notif(u,
                        f'Payroll Approved & Locked — {month_name} {instance.year} 🔒',
                        f'Payroll for {month_name} {instance.year} has been approved and locked. Payslips are being generated.',
                        'payroll_processed')

    except Exception as e:
        print(f"[NOTIF on_payroll_run] {e}")


# ─────────────────────────────────────────────
#  PAYROLL ENTRY — payslip ready (per employee)
# ─────────────────────────────────────────────
def on_payroll_entry(sender, instance, created, **kwargs):
    try:
        import calendar
        if not created and instance.payroll_run.status == 'approved':
            month_name = calendar.month_name[instance.payroll_run.month]
            net = float(instance.net_pay)
            create_notif(instance.employee,
                f'Payslip Ready — {month_name} {instance.payroll_run.year} 💰',
                f'Your payslip for {month_name} {instance.payroll_run.year} is ready. Net Pay: ₹{net:,.2f}. Download it from the Payroll section.',
                'payroll_processed')
    except Exception as e:
        print(f"[NOTIF on_payroll_entry] {e}")


# ─────────────────────────────────────────────
#  PAYROLL ADJUSTMENT — bonus / deduction added
# ─────────────────────────────────────────────
def on_payroll_adjustment(sender, instance, created, **kwargs):
    try:
        if created:
            import calendar
            run = instance.payroll_entry.payroll_run
            month_name = calendar.month_name[run.month]
            adj_type = instance.type.capitalize()
            amt = float(instance.amount)
            create_notif(instance.payroll_entry.employee,
                f'{adj_type} Added to Your Payroll 💼',
                f'A {adj_type} of ₹{amt:,.2f} has been added to your {month_name} {run.year} payroll. Reason: {instance.reason}',
                'payroll_processed')
    except Exception as e:
        print(f"[NOTIF on_payroll_adjustment] {e}")


# ─────────────────────────────────────────────
#  SALARY STRUCTURE — assigned / updated
# ─────────────────────────────────────────────
def on_salary_structure(sender, instance, created, **kwargs):
    try:
        if created:
            create_notif(instance.employee,
                'Salary Structure Assigned 💼',
                f'Your salary structure has been set effective {instance.effective_date}. CTC: ₹{float(instance.ctc):,.2f}.',
                'payroll_processed')
        else:
            create_notif(instance.employee,
                'Salary Structure Updated 🔄',
                f'Your salary structure has been updated (effective {instance.effective_date}). CTC: ₹{float(instance.ctc):,.2f}.',
                'payroll_processed')
    except Exception as e:
        print(f"[NOTIF on_salary_structure] {e}")


# ─────────────────────────────────────────────
#  EMPLOYEE PROFILE — department / manager change
# ─────────────────────────────────────────────
def on_employee_profile(sender, instance, created, **kwargs):
    try:
        if not created:
            create_notif(instance.user,
                'Your Profile Was Updated 👤',
                f'Your employee profile has been updated by HR/Admin. Please check your profile for details.',
                'general')
    except Exception as e:
        print(f"[NOTIF on_employee_profile] {e}")


# ─────────────────────────────────────────────
#  NEW USER ACCOUNT
# ─────────────────────────────────────────────
def on_new_user(sender, instance, created, **kwargs):
    try:
        if created:
            create_notif(instance,
                'Welcome to LAP System 👋',
                f'Hello {instance.get_full_name() or instance.username}! Your account has been created with role: {instance.role}. Please log in and update your profile.',
                'new_account')
    except Exception as e:
        print(f"[NOTIF on_new_user] {e}")


# ─────────────────────────────────────────────
#  HOLIDAY ADDED
# ─────────────────────────────────────────────
def on_holiday(sender, instance, created, **kwargs):
    try:
        if created:
            from accounts.models import User
            for user in User.objects.filter(is_active=True):
                create_notif(user,
                    f'Holiday Announced 🎉 — {instance.name}',
                    f'{instance.name} on {instance.date} has been added as a holiday.',
                    'general')
    except Exception as e:
        print(f"[NOTIF on_holiday] {e}")