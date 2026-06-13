from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0004_alter_permission_module'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rolepermission',
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
                max_length=20,
            ),
        ),
    ]
