# utils/migrations/0002_userpermissionoverride.py
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPermissionOverride',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('is_granted', models.BooleanField(default=True)),
                ('reason', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('granted_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='granted_overrides',
                    to=settings.AUTH_USER_MODEL
                )),
                ('permission', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='user_overrides', to='utils.permission'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='permission_overrides',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={'unique_together': {('user', 'permission')}, 'ordering': ['user__username', 'permission__module']},
        ),
    ]