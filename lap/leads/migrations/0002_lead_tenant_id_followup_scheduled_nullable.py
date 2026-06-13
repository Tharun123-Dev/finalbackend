from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lead',
            name='tenant_id',
            field=models.CharField(db_index=True, default='default', max_length=64),
        ),
        migrations.AlterField(
            model_name='followup',
            name='scheduled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
