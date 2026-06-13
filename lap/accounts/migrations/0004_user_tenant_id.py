from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_customrole_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='tenant_id',
            field=models.CharField(db_index=True, default='default', max_length=64),
        ),
    ]
