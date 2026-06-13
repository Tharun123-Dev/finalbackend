from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0002_lead_tenant_id_followup_scheduled_nullable'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='payment_reference',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
        migrations.AddField(
            model_name='lead',
            name='payment_status',
            field=models.CharField(default='Unpaid', max_length=50),
        ),
        migrations.AddField(
            model_name='lead',
            name='revenue_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ]
