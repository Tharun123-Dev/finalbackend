from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportTicketType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant_id', models.CharField(db_index=True, default='default', max_length=64)),
                ('name', models.CharField(max_length=100)),
                ('code', models.SlugField(max_length=80)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_support_ticket_types', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('tenant_id', 'code')},
            },
        ),
        migrations.CreateModel(
            name='SupportTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant_id', models.CharField(db_index=True, default='default', max_length=64)),
                ('ticket_no', models.CharField(blank=True, max_length=30, unique=True)),
                ('subject', models.CharField(max_length=180)),
                ('description', models.TextField()),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', max_length=20)),
                ('status', models.CharField(choices=[('open', 'Open'), ('in_progress', 'In Progress'), ('waiting_user', 'Waiting for User'), ('resolved', 'Resolved'), ('closed', 'Closed'), ('reopened', 'Reopened')], default='open', max_length=20)),
                ('resolution_note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_support_tickets', to=settings.AUTH_USER_MODEL)),
                ('issue_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tickets', to='support_tickets.supporttickettype')),
                ('requester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='support_tickets', to=settings.AUTH_USER_MODEL)),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resolved_support_tickets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at'],
                'indexes': [
                    models.Index(fields=['tenant_id', 'status'], name='support_tic_tenant__8d737a_idx'),
                    models.Index(fields=['tenant_id', 'requester'], name='support_tic_tenant__27bf74_idx'),
                    models.Index(fields=['tenant_id', 'priority'], name='support_tic_tenant__f1f47f_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='SupportTicketNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField()),
                ('status_from', models.CharField(blank=True, max_length=20)),
                ('status_to', models.CharField(blank=True, max_length=20)),
                ('is_internal', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='support_ticket_notes', to=settings.AUTH_USER_MODEL)),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='support_tickets.supportticket')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
