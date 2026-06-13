# payroll/migrations/XXXX_add_holiday_fields_to_payrollentry.py
# ── MIGRATION FILE ──
# Copy this file into: Backend/lap/payroll/migrations/
# Rename XXXX to the next migration number in that folder (e.g. 0007, 0008 etc.)
# Then run: python manage.py migrate

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # Change this to the name of the LAST migration in payroll/migrations/
        # e.g. ('payroll', '0006_some_previous_migration')
        ('payroll', '0001_initial'),  # ← UPDATE THIS to your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='payrollentry',
            name='holiday_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='payrollentry',
            name='holiday_names',
            field=models.JSONField(blank=True, default=list),
        ),
    ]