from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'

    def ready(self):
        from django.db.models.signals import post_save
        from django.apps import apps

        from notifications.signals import (
            on_leave_request,
            on_attendance_record,
            on_regularization,
            on_payroll_run,
            on_payroll_entry,
            on_payroll_adjustment,
            on_salary_structure,
            on_employee_profile,
            on_new_user,
            on_holiday,
        )

        LeaveRequest             = apps.get_model('leave',       'LeaveRequest')
        AttendanceRecord         = apps.get_model('attendance',  'AttendanceRecord')
        AttendanceRegularization = apps.get_model('attendance',  'AttendanceRegularization')
        PayrollRun               = apps.get_model('payroll',     'PayrollRun')
        PayrollEntry             = apps.get_model('payroll',     'PayrollEntry')
        PayrollAdjustment        = apps.get_model('payroll',     'PayrollAdjustment')
        SalaryStructure          = apps.get_model('payroll',     'SalaryStructure')
        EmployeeProfile          = apps.get_model('employees',   'EmployeeProfile')
        User                     = apps.get_model('accounts',    'User')
        Holiday                  = apps.get_model('attendance',  'Holiday')

        post_save.connect(on_leave_request,      sender=LeaveRequest,             dispatch_uid='notif_leave')
        post_save.connect(on_attendance_record,  sender=AttendanceRecord,         dispatch_uid='notif_attendance')
        post_save.connect(on_regularization,     sender=AttendanceRegularization, dispatch_uid='notif_regularize')
        post_save.connect(on_payroll_run,        sender=PayrollRun,               dispatch_uid='notif_payroll_run')
        post_save.connect(on_payroll_entry,      sender=PayrollEntry,             dispatch_uid='notif_payroll_entry')
        post_save.connect(on_payroll_adjustment, sender=PayrollAdjustment,        dispatch_uid='notif_payroll_adj')
        post_save.connect(on_salary_structure,   sender=SalaryStructure,          dispatch_uid='notif_salary')
        post_save.connect(on_employee_profile,   sender=EmployeeProfile,          dispatch_uid='notif_profile')
        post_save.connect(on_new_user,           sender=User,                     dispatch_uid='notif_new_user')
        post_save.connect(on_holiday,            sender=Holiday,                  dispatch_uid='notif_holiday')