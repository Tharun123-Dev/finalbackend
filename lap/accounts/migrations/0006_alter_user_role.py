from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_tenant_customrole_tenant_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('superadmin', 'SuperAdmin'),
                    ('admin', 'Admin'),
                    ('manager', 'Manager'),
                    ('hr', 'HR'),
                    ('counselor', 'Counselor'),
                    ('employee', 'Employee'),
                ],
                default='employee',
                max_length=20,
            ),
        ),
    ]
