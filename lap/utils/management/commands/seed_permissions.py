# utils/management/commands/seed_permissions.py
from django.core.management.base import BaseCommand
from utils.models import Permission, RolePermission
from utils.permission_registry import ALL_PERMISSIONS, ROLE_DEFAULTS


class Command(BaseCommand):
    help = 'Seed all permissions and assign defaults to roles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-roles',
            action='store_true',
            help='Reset role permissions to defaults (sets is_granted correctly)',
        )

    def handle(self, *args, **options):
        # ── Step 1: Create / update Permission rows ──────────────────────
        created_count = 0
        for code, label, module in ALL_PERMISSIONS:
            _, created = Permission.objects.update_or_create(
                code=code,
                defaults={'label': label, 'module': module},
            )
            if created:
                created_count += 1
                self.stdout.write(f'  + {code}')

        self.stdout.write(self.style.SUCCESS(
            f'OK Permissions: {created_count} new, {Permission.objects.count()} total'
        ))

        # ── Step 2: Optionally clear existing role permissions ────────────
        if options['reset_roles']:
            RolePermission.objects.all().delete()
            self.stdout.write('  Cleared existing role permissions')

        # ── Step 3: Seed RolePermission with is_granted=True ─────────────
        rp_created = rp_updated = 0
        all_roles = ['superadmin', 'admin', 'manager', 'hr', 'counselor', 'employee']

        for role in all_roles:
            granted_codes = set(ROLE_DEFAULTS.get(role, []))
            for code, _, _ in ALL_PERMISSIONS:
                try:
                    perm = Permission.objects.get(code=code)
                    should_grant = code in granted_codes
                    obj, created = RolePermission.objects.update_or_create(
                        role=role,
                        permission=perm,
                        defaults={'is_granted': should_grant},
                    )
                    if created:
                        rp_created += 1
                    else:
                        rp_updated += 1
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  Not found: {code}'))

        self.stdout.write(self.style.SUCCESS(
            f'OK Role permissions: {rp_created} created, {rp_updated} updated\n'
        ))
        self.stdout.write(self.style.SUCCESS('OK All permissions seeded correctly!'))
