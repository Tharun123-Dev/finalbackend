# Generated manually for separate day and night attendance records.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0004_attendance_night_shift_snapshots'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancerecord',
            name='shift_type',
            field=models.CharField(
                choices=[('day', 'Day Shift'), ('night', 'Night Shift')],
                default='day',
                max_length=10,
            ),
        ),
        migrations.AlterUniqueTogether(
            name='attendancerecord',
            unique_together={('employee', 'date', 'shift_type')},
        ),
    ]
