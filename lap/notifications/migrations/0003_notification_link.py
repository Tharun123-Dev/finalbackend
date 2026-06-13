# notifications/migrations/0003_notification_link.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_systemsetting_value_type_alter_notification_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='link',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
    ]