from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('body', models.TextField()),
                ('type', models.CharField(
                    choices=[
                        ('leave_applied',    'Leave Applied'),
                        ('leave_approved',   'Leave Approved'),
                        ('leave_rejected',   'Leave Rejected'),
                        ('leave_cancelled',  'Leave Cancelled'),
                        ('attendance_absent','Attendance Absent'),
                        ('regularization',   'Regularization Request'),
                        ('payroll_processed','Payroll Processed'),
                        ('leave_balance_low','Leave Balance Low'),
                        ('new_account',      'New Account Created'),
                        ('general',          'General'),
                    ],
                    default='general', max_length=30
                )),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='accounts.user')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='SystemSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=100, unique=True)),
                ('value', models.TextField()),
                ('label', models.CharField(max_length=200)),
                ('category', models.CharField(
                    choices=[
                        ('attendance', 'Attendance'),
                        ('leave',      'Leave'),
                        ('payroll',    'Payroll'),
                        ('general',    'General'),
                    ],
                    default='general', max_length=30
                )),
                ('description', models.TextField(blank=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='updated_settings',
                    to='accounts.user'
                )),
            ],
            options={'ordering': ['category', 'key']},
        ),
    ]