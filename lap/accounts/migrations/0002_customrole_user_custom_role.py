# accounts/migrations/0002_customrole_user_custom_role.py
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('display_name', models.CharField(max_length=100)),
                ('level', models.IntegerField(default=10)),
                ('base_role', models.CharField(max_length=20, default='employee')),
                ('is_active', models.BooleanField(default=True)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['level', 'name']},
        ),
        migrations.AddField(
            model_name='user',
            name='custom_role',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='users', to='accounts.customrole'
            ),
        ),
    ]