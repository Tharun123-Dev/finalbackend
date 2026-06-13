# affiliate/migrations/0001_initial.py
import uuid
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
            name='Affiliate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('referral_code', models.CharField(db_index=True, max_length=20, unique=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('bank_account_details', models.CharField(blank=True, max_length=255, null=True)),
                ('bank_name', models.CharField(blank=True, max_length=100, null=True)),
                ('account_number', models.CharField(blank=True, max_length=50, null=True)),
                ('payout_method', models.CharField(default='ACH/Direct Deposit', max_length=50)),
                ('upi_id', models.CharField(blank=True, max_length=100, null=True)),
                ('profile_image_url', models.URLField(blank=True, null=True)),
                ('total_earnings', models.FloatField(default=0.0)),
                ('paid_earnings', models.FloatField(default=0.0)),
                ('total_clicks', models.IntegerField(default=0)),
                ('active_campaigns', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='affiliate_profile',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Referral',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('customer_name', models.CharField(max_length=150)),
                ('customer_email', models.EmailField()),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('converted', 'Converted'), ('rejected', 'Rejected')],
                    default='pending', max_length=20
                )),
                ('purchase_amount', models.FloatField(default=0.0)),
                ('referred_at', models.DateTimeField(auto_now_add=True)),
                ('affiliate', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='referrals',
                    to='affiliate.affiliate'
                )),
            ],
            options={'ordering': ['-referred_at']},
        ),
        migrations.CreateModel(
            name='Commission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.FloatField()),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('paid', 'Paid')],
                    default='pending', max_length=20
                )),
                ('payment_date', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('affiliate', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='commissions',
                    to='affiliate.affiliate'
                )),
                ('referral', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='commission',
                    to='affiliate.referral'
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.FloatField()),
                ('payment_method', models.CharField(blank=True, max_length=50, null=True)),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('status', models.CharField(
                    choices=[('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')],
                    default='processing', max_length=20
                )),
                ('paid_at', models.DateTimeField(auto_now_add=True)),
                ('affiliate', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='payments',
                    to='affiliate.affiliate'
                )),
            ],
            options={'ordering': ['-paid_at']},
        ),
        migrations.CreateModel(
            name='AffiliateNotification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('type', models.CharField(
                    choices=[('commission', 'Commission'), ('referral', 'Referral'),
                             ('payment', 'Payment'), ('system', 'System')],
                    default='system', max_length=20
                )),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('affiliate', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='affiliate_notifications',
                    to='affiliate.affiliate'
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]