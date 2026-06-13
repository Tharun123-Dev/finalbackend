from django.db import migrations, models


def seed_lead_options(apps, schema_editor):
    LeadOption = apps.get_model('leads', 'LeadOption')
    defaults = [
        ('status', 'New', 'New', 10),
        ('status', 'Contacted', 'Contacted', 20),
        ('status', 'Interested', 'Interested', 30),
        ('status', 'Follow-Up Pending', 'Follow-Up Pending', 40),
        ('status', 'Admission Confirmed', 'Admission Confirmed', 50),
        ('status', 'Rejected', 'Rejected', 60),
        ('contact_method', 'Phone Call', 'Call', 10),
        ('contact_method', 'WhatsApp', 'WhatsApp', 20),
        ('contact_method', 'Email', 'Email', 30),
        ('contact_method', 'Meeting Visit', 'Meeting', 40),
    ]
    for category, label, value, sort_order in defaults:
        LeadOption.objects.get_or_create(
            tenant_id='default',
            category=category,
            value=value,
            defaults={
                'label': label,
                'sort_order': sort_order,
                'is_active': True,
                'is_system': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0003_lead_revenue_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeadOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant_id', models.CharField(db_index=True, default='default', max_length=64)),
                ('category', models.CharField(choices=[('status', 'Status'), ('contact_method', 'Contact Method')], max_length=30)),
                ('label', models.CharField(max_length=100)),
                ('value', models.CharField(max_length=100)),
                ('color', models.CharField(blank=True, default='', max_length=30)),
                ('sort_order', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('is_system', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'lead_options',
                'ordering': ['category', 'sort_order', 'id'],
                'unique_together': {('tenant_id', 'category', 'value')},
            },
        ),
        migrations.AlterField(
            model_name='lead',
            name='status',
            field=models.CharField(default='New', max_length=50),
        ),
        migrations.RunPython(seed_lead_options, migrations.RunPython.noop),
    ]
