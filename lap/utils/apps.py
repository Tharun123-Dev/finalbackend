# utils/apps.py
# FIX: Removed DB access in ready() — caused RuntimeWarning.
# Permissions are now seeded ONCE via management command only.
from django.apps import AppConfig


class UtilsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'utils'

    def ready(self):
        # DO NOTHING HERE.
        # Run this once manually after first migrate:
        #   python manage.py seed_permissions
        # Never query DB inside ready() — Django raises RuntimeWarning.
        pass