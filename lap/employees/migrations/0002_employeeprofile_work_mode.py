from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeeprofile',
            name='work_mode',
            field=models.CharField(
                choices=[
                    ('office', 'Work From Office'),
                    ('work_from_home', 'Work From Home'),
                ],
                default='office',
                max_length=20,
            ),
        ),
    ]
