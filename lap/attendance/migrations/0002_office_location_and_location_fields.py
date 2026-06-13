# attendance/migrations/0002_office_location_and_location_fields.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0001_initial'),
    ]

    operations = [
        # ── 1. New OfficeLocation table ───────────────────────────────────────
        migrations.CreateModel(
            name='OfficeLocation',
            fields=[
                ('id',             models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name',           models.CharField(default='Head Office', max_length=100)),
                ('latitude',       models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude',      models.DecimalField(decimal_places=6, max_digits=9)),
                ('radius_meters',  models.PositiveIntegerField(default=300,
                                   help_text='Allowed check-in radius in metres')),
                ('is_active',      models.BooleanField(default=True)),
                ('created_at',     models.DateTimeField(auto_now_add=True)),
                ('updated_at',     models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-is_active', '-updated_at'],
            },
        ),

        # ── 2. Location columns on AttendanceRecord ───────────────────────────
        migrations.AddField(
            model_name='attendancerecord',
            name='checkin_latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='checkin_longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='checkout_latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='checkout_longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='checkin_distance_m',
            field=models.FloatField(blank=True,
                                    help_text='Distance from office at check-in (metres)',
                                    null=True),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='checkout_distance_m',
            field=models.FloatField(blank=True,
                                    help_text='Distance from office at check-out (metres)',
                                    null=True),
        ),
    ]