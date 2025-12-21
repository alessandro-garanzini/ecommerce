# Django Groups & Permissions - Authentication System

## Overview

The authentication system now uses **Django's built-in Groups and Permissions** instead of hardcoded boolean flags (`is_customer`, etc.). This provides a more flexible, scalable, and Django-native approach to role management.

## Architecture Changes

### ✅ What Changed

1. **Removed `is_customer` field** - Replaced with Django Groups
2. **Added `UserGroups` constants** - For consistent group naming
3. **Role-based methods** - User model now has `is_customer`, `is_admin`, `is_staff_member` as properties that check group membership
4. **Updated managers** - `create_customer()`, `create_staff_user()` now automatically assign groups
5. **New auth classes** - Added `StaffJWTAuth` for granular access control
6. **Management command** - `init_groups` to initialize groups on first setup

### 🎯 Benefits

- **Django-native** - Uses standard Django permissions system
- **Flexible** - Users can belong to multiple groups
- **Scalable** - Easy to add new groups and permissions
- **Admin-friendly** - Groups visible/editable in Django admin
- **Future-proof** - Ready for complex permission requirements

## User Groups

### Available Groups

| Group | Purpose | Created By |
|-------|---------|------------|
| **Customer** | Regular ecommerce customers | `User.objects.create_customer()` |
| **Staff** | Backend staff with limited admin access | `User.objects.create_staff_user()` |
| **Admin** | Full system administrators | `User.objects.create_superuser()` |

### Group Assignment

Groups are automatically assigned during user creation:

```python
# Create a customer
user = User.objects.create_customer(
    email='customer@example.com',
    password='securepass123'
)
# User is automatically added to "Customer" group

# Create a staff user
user = User.objects.create_staff_user(
    email='staff@example.com',
    password='securepass123'
)
# User is automatically added to "Staff" group

# Create an admin
user = User.objects.create_superuser(
    email='admin@example.com',
    password='securepass123'
)
# User is automatically added to "Admin" group
```

## User Model API

### Role Checking (Properties)

```python
user = User.objects.get(email='user@example.com')

# Check if user is a customer
if user.is_customer:
    print("User is a customer")

# Check if user is a staff member
if user.is_staff_member:
    print("User is staff")

# Check if user is an admin
if user.is_admin:
    print("User is an admin")

# Get role display name
print(user.get_role_display())  # "Customer", "Staff", "Admin", etc.
```

### Group Management

```python
from accounts.models import UserGroups

user = User.objects.get(email='user@example.com')

# Add user to a group
user.add_to_group(UserGroups.STAFF)

# Remove from a group
user.remove_from_group(UserGroups.CUSTOMER)

# Check group membership
if user.is_in_group(UserGroups.ADMIN):
    print("User is in Admin group")

# Get all user groups
groups = user.groups.all()
group_names = list(user.groups.values_list('name', flat=True))
```

## API Changes

### Registration Endpoint

Now accepts `role` parameter instead of `is_customer`:

```bash
# Register as customer (default)
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "customer"
  }'

# Register as staff
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "staff@example.com",
    "password": "securepass123",
    "role": "staff"
  }'

# Register as admin (requires additional security checks in production)
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "securepass123",
    "role": "admin"
  }'
```

Valid roles: `customer`, `staff`, `admin`

### User Profile Response

The `/api/auth/me` endpoint now includes groups and role:

```json
{
  "id": 1,
  "email": "customer@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_staff": false,
  "is_customer": true,
  "is_active": true,
  "role": "Customer",
  "groups": ["Customer"],
  "date_joined": "2025-12-21T20:15:48.491Z"
}
```

## Authentication Classes

### Available Auth Classes

```python
from accounts.auth import jwt_auth, admin_jwt_auth, staff_jwt_auth, customer_jwt_auth

# Any authenticated user
@router.get('/protected', auth=jwt_auth)
def protected_endpoint(request):
    return {"user": request.auth.email}

# Admin only
@router.get('/admin/data', auth=admin_jwt_auth)
def admin_endpoint(request):
    return {"message": "Admin access granted"}

# Staff only (includes both Staff group and is_staff=True users)
@router.get('/staff/dashboard', auth=staff_jwt_auth)
def staff_endpoint(request):
    return {"message": "Staff access granted"}

# Customer only
@router.get('/customer/orders', auth=customer_jwt_auth)
def customer_endpoint(request):
    return {"message": "Customer access granted"}
```

## Permissions System

### Adding Permissions to Groups

When you create new models (e.g., Order, Product), you can assign permissions to groups:

```python
# In your management command or migration
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from accounts.models import UserGroups
from myapp.models import Order, Product

# Get groups
customer_group = Group.objects.get(name=UserGroups.CUSTOMER)
staff_group = Group.objects.get(name=UserGroups.STAFF)
admin_group = Group.objects.get(name=UserGroups.ADMIN)

# Get permissions
view_order = Permission.objects.get(codename='view_order')
add_order = Permission.objects.get(codename='add_order')
change_order = Permission.objects.get(codename='change_order')
view_product = Permission.objects.get(codename='view_product')

# Assign to customer group
customer_group.permissions.add(view_order, add_order, view_product)

# Assign to staff group
staff_group.permissions.add(view_order, change_order, view_product)

# Admins get all permissions via is_superuser flag
```

### Checking Permissions in Views

```python
from ninja import Router
from accounts.auth import jwt_auth

router = Router()

@router.post('/orders', auth=jwt_auth)
def create_order(request):
    # Check if user has permission
    if not request.auth.has_perm('orders.add_order'):
        return 403, {"error": "Permission denied"}
    
    # Create order logic
    return {"success": True}
```

### Decorators for Permissions

```python
from django.contrib.auth.decorators import permission_required
from ninja.decorators import decorate_view

@router.get('/admin/users', auth=jwt_auth)
@decorate_view(permission_required('auth.view_user', raise_exception=True))
def list_users(request):
    users = User.objects.all()
    return {"users": [u.email for u in users]}
```

## Setup & Initialization

### 1. Run Migrations

```bash
docker compose exec api python manage.py migrate
```

### 2. Initialize Groups

```bash
docker compose exec api python manage.py init_groups
```

This creates the three default groups: Customer, Staff, Admin

### 3. Create Initial Users

```bash
# Create superuser
docker compose exec api python manage.py createsuperuser

# Or via API
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123", "role": "admin"}'
```

## Django Admin Interface

### Managing Groups

1. Login to Django admin: http://localhost:8000/admin/
2. Navigate to **Authentication and Authorization > Groups**
3. Select a group to edit permissions
4. Assign/remove permissions as needed

### Managing Users

1. Navigate to **Accounts > Users**
2. Select a user
3. In "Permissions" section:
   - Assign to groups using the **Groups** field
   - Assign individual permissions using **User permissions**
4. The "Role" column shows the user's primary role

## Migration from Old System

If you have existing data with `is_customer` field:

### Step 1: Create Data Migration

```bash
docker compose exec api python manage.py makemigrations accounts --empty --name migrate_customers_to_groups
```

### Step 2: Edit Migration

```python
from django.db import migrations
from django.contrib.auth.models import Group

def migrate_customers_to_groups(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    customer_group, _ = Group.objects.get_or_create(name='Customer')
    
    # Add all users with is_customer=True to Customer group
    customers = User.objects.filter(is_customer=True)
    for user in customers:
        user.groups.add(customer_group)

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_remove_is_customer_field'),
    ]
    
    operations = [
        migrations.RunPython(migrate_customers_to_groups),
    ]
```

### Step 3: Run Migration

```bash
docker compose exec api python manage.py migrate
```

## Advanced: Custom Permissions

### Define Custom Permissions in Model

```python
class Order(models.Model):
    # ... fields ...
    
    class Meta:
        permissions = [
            ("cancel_order", "Can cancel orders"),
            ("refund_order", "Can process refunds"),
        ]
```

### Assign Custom Permissions

```python
from django.contrib.auth.models import Group, Permission

staff_group = Group.objects.get(name='Staff')
cancel_perm = Permission.objects.get(codename='cancel_order')
refund_perm = Permission.objects.get(codename='refund_order')

staff_group.permissions.add(cancel_perm, refund_perm)
```

### Check Custom Permissions

```python
if user.has_perm('orders.cancel_order'):
    # Allow cancellation
    pass
```

## Best Practices

### 1. Use Groups for Roles

```python
# ✅ Good: Use groups
user.add_to_group(UserGroups.STAFF)

# ❌ Bad: Custom boolean fields
user.is_staff_member = True
```

### 2. Check Permissions, Not Groups

```python
# ✅ Good: Check permission
if user.has_perm('orders.change_order'):
    # Edit order

# ❌ Bad: Check group directly (less flexible)
if user.is_in_group('Staff'):
    # Edit order
```

### 3. Assign Permissions to Groups, Not Users

```python
# ✅ Good: Assign to group
staff_group.permissions.add(permission)

# ❌ Bad: Assign to individual users (hard to manage)
user.user_permissions.add(permission)
```

### 4. Document Group Permissions

Keep documentation of which permissions each group should have:

```python
# In init_groups.py management command
CUSTOMER_PERMISSIONS = [
    'orders.view_order',
    'orders.add_order',
    'products.view_product',
]

STAFF_PERMISSIONS = CUSTOMER_PERMISSIONS + [
    'orders.change_order',
    'orders.delete_order',
    'products.change_product',
]
```

## Testing

### Test Group Assignment

```python
def test_customer_creation():
    user = User.objects.create_customer(
        email='test@example.com',
        password='testpass123'
    )
    assert user.is_customer
    assert user.is_in_group(UserGroups.CUSTOMER)
    assert not user.is_staff
```

### Test Permissions

```python
def test_staff_permissions():
    user = User.objects.create_staff_user(
        email='staff@example.com',
        password='testpass123'
    )
    
    # Add permission to Staff group
    from django.contrib.auth.models import Group, Permission
    staff_group = Group.objects.get(name='Staff')
    permission = Permission.objects.get(codename='view_order')
    staff_group.permissions.add(permission)
    
    assert user.has_perm('orders.view_order')
```

## Summary

The new Groups & Permissions system provides:

- ✅ **Django-native**: Uses standard Django patterns
- ✅ **Flexible**: Easy to add new roles and permissions
- ✅ **Scalable**: Ready for complex authorization requirements  
- ✅ **Maintainable**: Clear separation of roles and permissions
- ✅ **Future-proof**: Can grow with your application needs

For questions or custom permission setups, refer to [Django's permissions documentation](https://docs.djangoproject.com/en/stable/topics/auth/default/#permissions-and-authorization).
