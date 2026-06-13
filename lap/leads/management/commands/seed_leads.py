from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from leads.models import Lead, LeadForm, LeadField, LeadFieldValue, LeadStatus, FieldType
from datetime import datetime, timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed initial lead module data'

    def handle(self, *args, **options):
        # Create the Active Intake Form
        form, created = LeadForm.objects.get_or_create(
            name='Active Intake Form',
            defaults={'description': 'Comprehensive student intake form'}
        )

        if created:
            fields_data = [
                {
                    'label': 'Student Full Name',
                    'field_type': FieldType.TEXT,
                    'required': True,
                    'placeholder': "Enter student's full name",
                    'section': 'Basic Info',
                    'validation': {'minLength': 2},
                    'is_core': True,
                    'order': 1
                },
                {
                    'label': 'Email Address',
                    'field_type': FieldType.EMAIL,
                    'required': True,
                    'placeholder': 'studentname@example.com',
                    'section': 'Basic Info',
                    'is_core': True,
                    'order': 2
                },
                {
                    'label': 'Phone Number',
                    'field_type': FieldType.NUMBER,
                    'required': True,
                    'placeholder': 'e.g., 9876543210',
                    'section': 'Basic Info',
                    'is_core': True,
                    'order': 3
                },
                {
                    'label': 'Course of Interest',
                    'field_type': FieldType.DROPDOWN,
                    'required': True,
                    'placeholder': 'Select a course',
                    'section': 'Academic Info',
                    'options': ['B.Tech Computer Science', 'MBA', 'M.Tech Data Science',
                                'B.Sc Psychology', 'Digital Marketing'],
                    'is_core': True,
                    'order': 4
                },
                {
                    'label': 'Source',
                    'field_type': FieldType.DROPDOWN,
                    'required': False,
                    'placeholder': 'How did you hear about us?',
                    'section': 'Marketing Info',
                    'options': ['Google Search', 'LinkedIn', 'Facebook Ads',
                                'Instagram', 'Referral', 'Educational Fair'],
                    'is_core': True,
                    'order': 5
                },
                {
                    'label': 'Internal Notes',
                    'field_type': FieldType.TEXTAREA,
                    'required': False,
                    'section': 'Administration',
                    'is_core': True,
                    'order': 6
                },
            ]
            for fd in fields_data:
                LeadField.objects.create(form=form, **fd)

            self.stdout.write(self.style.SUCCESS('Created Active Intake Form with fields'))
        else:
            self.stdout.write('Active Intake Form already exists, skipping form creation')

        self.stdout.write(self.style.SUCCESS('Lead seed completed successfully!'))