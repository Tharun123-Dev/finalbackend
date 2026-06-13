# notifications/utils.py
"""
Smart notification utilities.
All notification dispatching goes through here so it respects permissions.
"""
from django.conf import settings


def notify_user(user, title, body, notif_type='general'):
    """Send notification to a single user."""
    from .models import Notification
    Notification.objects.create(
        user=user, title=title, body=body, type=notif_type
    )


def notify_role(roles, title, body, notif_type='general', exclude_user=None):
    """
    Send notification to all users whose BASE role is in `roles`.
    Only sends to active users.
    """
    from accounts.models import User
    from .models import Notification

    qs = User.objects.filter(role__in=roles, is_active=True)
    if exclude_user:
        qs = qs.filter(tenant_id=getattr(exclude_user, 'tenant_id', 'default'))
    if exclude_user:
        qs = qs.exclude(pk=exclude_user.pk)

    notifications = [
        Notification(user=u, title=title, body=body, type=notif_type)
        for u in qs
    ]
    Notification.objects.bulk_create(notifications)


def notify_permission(perm_code, title, body, notif_type='general', exclude_user=None):
    """
    Send notification to all users who have a specific permission (role-level OR override).
    This is the key function — only people who CAN act on something get notified.
    """
    from accounts.models import User
    from utils.models import UserPermissionOverride
    from .models import Notification

    all_user_ids = set(
        UserPermissionOverride.objects.filter(
            permission__code=perm_code, is_granted=True
        ).values_list('user_id', flat=True)
    )
    all_user_ids.update(User.objects.filter(is_superuser=True, is_active=True).values_list('id', flat=True))

    if exclude_user:
        all_user_ids.discard(exclude_user.pk)

    target_users = User.objects.filter(id__in=all_user_ids, is_active=True)
    if exclude_user:
        target_users = target_users.filter(tenant_id=getattr(exclude_user, 'tenant_id', 'default'))

    notifications = [
        Notification(user=u, title=title, body=body, type=notif_type)
        for u in target_users
    ]
    Notification.objects.bulk_create(notifications)


def notify_leave_applied(leave_request):
    """
    When employee applies leave:
    - Notify everyone with 'approve_leave' permission (managers, HR, admin with that perm)
    - Include who applied, what type, how many days
    """
    from accounts.models import User

    emp = leave_request.employee
    emp_name = emp.get_full_name() or emp.username
    emp_role = emp.get_display_role()
    lt = leave_request.leave_type.name
    days = leave_request.days
    start = leave_request.start_date
    end = leave_request.end_date

    title = f"Leave Request: {emp_name}"
    body = (
        f"{emp_name} ({emp_role}) has applied for {lt} "
        f"from {start} to {end} ({days} day{'s' if days != 1 else ''}).\n"
        f"Reason: {leave_request.reason}"
    )

    notify_permission(
        perm_code='approve_leave',
        title=title,
        body=body,
        notif_type='leave_applied',
        exclude_user=emp
    )
    # Also confirm to the employee
    notify_user(
        emp,
        title=f"Leave Application Submitted",
        body=f"Your {lt} application ({days} day{'s' if days != 1 else ''}) from {start} to {end} has been submitted and is pending approval.",
        notif_type='leave_applied'
    )


def notify_leave_actioned(leave_request, action, actioned_by):
    """
    When leave is approved/rejected — tell the employee who did it and their role.
    """
    emp = leave_request.employee
    lt  = leave_request.leave_type.name
    approver_name = actioned_by.get_full_name() or actioned_by.username
    approver_role = actioned_by.get_display_role()
    action_upper  = action.upper()

    title = f"Leave {action_upper}: {lt}"
    body = (
        f"Your {lt} application ({leave_request.days} day(s), "
        f"{leave_request.start_date} – {leave_request.end_date}) has been "
        f"{action} by {approver_name} ({approver_role})."
    )
    if leave_request.approver_note:
        body += f"\nNote: {leave_request.approver_note}"

    notify_user(emp, title=title, body=body,
                notif_type=f'leave_{action}')


def notify_attendance_regularization(regularization):
    """
    When employee requests attendance correction — notify those with approve_regularization perm.
    Show approved_by with username + role in subsequent notification.
    """
    emp = regularization.employee
    emp_name = emp.get_full_name() or emp.username
    emp_role = emp.get_display_role()
    date = regularization.attendance.date

    notify_permission(
        perm_code='approve_regularization',
        title=f"Regularization Request: {emp_name}",
        body=(
            f"{emp_name} ({emp_role}) has requested attendance correction for {date}.\n"
            f"Reason: {regularization.reason}"
        ),
        notif_type='regularization',
        exclude_user=emp
    )


def notify_regularization_actioned(regularization, action, actioned_by):
    emp = regularization.employee
    approver_name = actioned_by.get_full_name() or actioned_by.username
    approver_role = actioned_by.get_display_role()
    date = regularization.attendance.date

    notify_user(
        emp,
        title=f"Attendance Correction {action.upper()}: {date}",
        body=(
            f"Your attendance correction request for {date} has been "
            f"{action} by {approver_name} ({approver_role})."
        ),
        notif_type='regularization'
    )


def notify_new_employee(new_user, created_by):
    """Notify admins + superadmin when a new employee is added."""
    name = new_user.get_full_name() or new_user.username
    creator_name = created_by.get_full_name() or created_by.username
    creator_role = created_by.get_display_role()

    notify_permission(
        perm_code='view_employees',
        title=f"New Employee: {name}",
        body=(
            f"{name} ({new_user.get_display_role()}) has been added by "
            f"{creator_name} ({creator_role})."
        ),
        notif_type='new_account',
        exclude_user=created_by
    )


def notify_payroll_processed(payroll_run, processed_by):
    """Notify all active employees that payroll is processed."""
    from accounts.models import User
    from .models import Notification

    processor_name = processed_by.get_full_name() or processed_by.username
    processor_role = processed_by.get_display_role()
    month_year = f"{payroll_run.month}/{payroll_run.year}"

    employees = User.objects.filter(is_active=True, tenant_id=getattr(processed_by, 'tenant_id', 'default'))
    notifications = [
        Notification(
            user=u,
            title=f"Payslip Ready: {month_year}",
            body=(
                f"Your payslip for {month_year} has been processed by "
                f"{processor_name} ({processor_role}). Check the Payroll section."
            ),
            type='payroll_processed'
        )
        for u in employees
    ]
    Notification.objects.bulk_create(notifications)
