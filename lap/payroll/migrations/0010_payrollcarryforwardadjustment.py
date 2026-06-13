from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0005_attendancerecord_shift_type_unique'),
        ('payroll', '0009_payrollentry_comp_off_days_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PayrollCarryForwardAdjustment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_month', models.IntegerField()),
                ('source_year', models.IntegerField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('reason', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('applied', 'Applied'), ('ignored', 'Ignored')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('applied_at', models.DateTimeField(blank=True, null=True)),
                ('applied_entry', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='applied_carry_forward_adjustments', to='payroll.payrollentry')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payroll_carry_forward_adjustments', to=settings.AUTH_USER_MODEL)),
                ('source_regularization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payroll_corrections', to='attendance.attendanceregularization')),
                ('source_run', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='carry_forward_sources', to='payroll.payrollrun')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
