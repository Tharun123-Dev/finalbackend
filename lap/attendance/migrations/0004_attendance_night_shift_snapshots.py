# Generated manually for night-shift attendance policy snapshots.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0003_alter_attendancerecord_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancerecord',
            name='check_in_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='check_out_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='shift_start_snapshot',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='shift_end_snapshot',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='grace_minutes_snapshot',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='standard_hours_snapshot',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='half_day_hours_snapshot',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='is_overnight_shift',
            field=models.BooleanField(default=False),
        ),
    ]
