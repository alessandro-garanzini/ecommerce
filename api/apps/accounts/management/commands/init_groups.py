from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import UserGroups


class Command(BaseCommand):
    help = 'Initialize user groups and permissions for the ecommerce application'

    def handle(self, *args, **options):
        self.stdout.write('Initializing user groups...')
        
        # Create groups
        customer_group, created = Group.objects.get_or_create(name=UserGroups.CUSTOMER)
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created group: {UserGroups.CUSTOMER}'))
        else:
            self.stdout.write(f'  Group already exists: {UserGroups.CUSTOMER}')
        
        staff_group, created = Group.objects.get_or_create(name=UserGroups.STAFF)
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created group: {UserGroups.STAFF}'))
        else:
            self.stdout.write(f'  Group already exists: {UserGroups.STAFF}')
        
        admin_group, created = Group.objects.get_or_create(name=UserGroups.ADMIN)
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created group: {UserGroups.ADMIN}'))
        else:
            self.stdout.write(f'  Group already exists: {UserGroups.ADMIN}')
        
        # Assign basic permissions to groups
        # You can customize these based on your models
        
        # Customer permissions (example - customize based on your ecommerce models)
        customer_permissions = []
        # When you create Order, Product models, add permissions like:
        # customer_permissions = Permission.objects.filter(
        #     codename__in=['view_order', 'add_order', 'view_product']
        # )
        customer_group.permissions.set(customer_permissions)
        
        # Staff permissions (more access than customers)
        staff_permissions = []
        # staff_permissions = Permission.objects.filter(
        #     codename__in=['view_order', 'change_order', 'view_product', 'view_user']
        # )
        staff_group.permissions.set(staff_permissions)
        
        # Admin permissions (all permissions)
        # Admins typically get permissions through is_superuser flag
        # But you can also assign specific permissions here if needed
        admin_permissions = []
        admin_group.permissions.set(admin_permissions)
        
        self.stdout.write(self.style.SUCCESS('\n✓ Successfully initialized user groups and permissions'))
        self.stdout.write('\nAvailable groups:')
        self.stdout.write(f'  - {UserGroups.CUSTOMER}: For ecommerce customers')
        self.stdout.write(f'  - {UserGroups.STAFF}: For backend staff members')
        self.stdout.write(f'  - {UserGroups.ADMIN}: For system administrators')
        self.stdout.write('\nNote: Customize permissions in this command as you add more models.')
