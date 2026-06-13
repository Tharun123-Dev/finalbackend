import calendar
from datetime import date

from django.db import migrations, models


def fill_existing_periods(apps, schema_editor):
    PayrollRun = apps.get_model('payroll', 'PayrollRun')
    for run in PayrollRun.objects.all():
        last_day = calendar.monthrange(run.year, run.month)[1]
        run.period_start = date(run.year, run.month, 1)
        run.period_end = date(run.year, run.month, last_day)
        run.save(update_fields=['period_start', 'period_end'])


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0010_payrollcarryforwardadjustment'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='payrollrun',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='payrollrun',
            name='period_start',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payrollrun',
            name='period_end',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.RunPython(fill_existing_periods, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='payrollrun',
            unique_together={('month', 'year', 'period_start', 'period_end')},
        ),
        migrations.AlterModelOptions(
            name='payrollrun',
            options={'ordering': ['-year', '-month', '-period_start']},
        ),
    ]
