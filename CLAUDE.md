# GitHub Copilot Instructions - E-commerce Backend Project

## Project Overview

This is a **backend-only e-commerce platform** built with:
- **Django 6.0** - Core framework
- **Django Ninja 1.5.1** - Modern async-capable REST API framework
- **PostgreSQL 16** - Primary database
- **Redis 7** - Caching and rate limiting
- **Docker & Docker Compose** - Containerized development environment

## Technology Stack

### Core Technologies
- **Python 3.12**
- **Django Ninja** for API endpoints (NOT Django REST Framework)
- **django-ninja-jwt 5.3.5** for JWT authentication
- **django-auditlog 3.4.1** for model change tracking
- **pytest & pytest-django** for testing
- **model-bakery** for test data generation

### Key Libraries
- `django-cors-headers` - CORS support for frontend integration
- `psycopg2-binary` - PostgreSQL adapter
- `redis` - Redis client

## Project Structure

All Django apps should be placed in `api/apps/` directory and follow this standardized structure:

```
api/apps/<app_name>/
├── __init__.py
├── apps.py                       # App configuration
├── admin.py                      # Django admin customization
├── api.py                        # Django Ninja API endpoints (router)
├── auth.py                       # Custom authentication classes (if needed)
├── managers.py                   # Custom model managers
├── models/
│   ├── __init__.py
│   └── <model_name>.py          # One file per model
├── schemas/
│   ├── __init__.py              # Export all schemas
│   ├── auth.py                  # Authentication-related schemas
│   ├── user.py                  # User-related schemas (use ModelSchema when possible)
│   ├── <category>.py            # Schemas organized by category
│   └── common.py                # Shared/generic schemas
├── services/
│   ├── __init__.py
│   └── <service_name>.py        # Business logic layer
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── <command_name>.py    # Django management commands
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py
└── tests/
    ├── __init__.py
    ├── conftest.py              # Pytest fixtures
    ├── test_api.py              # API endpoint tests
    ├── test_models.py           # Model tests
    ├── test_services.py         # Service layer tests
    ├── test_schemas.py          # Schema validation tests
    └── test_auth.py             # Authentication tests (if applicable)
```

### Example: Accounts App Structure
The `accounts` app serves as the reference implementation:

```
api/apps/accounts/
├── models/
│   ├── user.py                  # Custom User model with Groups-based roles
│   └── password_reset_token.py # Password reset functionality
├── schemas/
│   ├── auth.py                  # RegisterSchema, LoginSchema, TokenResponseSchema
│   ├── user.py                  # UserSchema (ModelSchema)
│   ├── password_reset.py        # Password reset schemas
│   └── common.py                # MessageSchema
├── services/
│   ├── auth_service.py          # Registration, rate limiting, password reset
│   └── oauth_provider.py        # Future OAuth integration (placeholder)
├── management/commands/
│   └── init_groups.py           # Initialize Customer, Staff, Admin groups
└── tests/
    ├── conftest.py              # Shared fixtures (users, tokens, auth headers)
    ├── test_api.py              # 23 tests for API endpoints
    ├── test_models.py           # 21 tests for User model
    ├── test_services.py         # 17 tests for AuthService
    ├── test_schemas.py          # 19 tests for schema validation
    └── test_auth.py             # 12 tests for JWT authentication
```

## Authentication System

The project uses a **robust JWT-based authentication system** with role-based access control:

### Authentication Features
- **Email-only authentication** (no username field)
- **JWT tokens** via `django-ninja-jwt` (access: 15 min, refresh: 7 days)
- **Django Groups-based roles**: Customer, Staff, Admin
- **Rate limiting** via Redis (login attempts, password reset)
- **Password reset flow** with secure token generation
- **Multiple auth classes** for granular endpoint protection:
  - `JWTAuth` - Basic JWT authentication
  - `AdminJWTAuth` - Admin/superuser only
  - `StaffJWTAuth` - Staff and admin users
  - `CustomerJWTAuth` - Customer users only

### Custom User Model
- Uses Django's built-in Groups system (NOT boolean flags)
- Custom managers: `create_customer()`, `create_staff_user()`, `create_superuser()`
- Properties: `is_customer`, `is_staff_member`, `is_admin`
- Methods: `add_to_group()`, `remove_from_group()`, `get_role_display()`

### Key Authentication Files
- `api/apps/accounts/auth.py` - JWT authentication classes
- `api/apps/accounts/models/user.py` - Custom User model
- `api/apps/accounts/managers.py` - User creation methods
- `api/apps/accounts/services/auth_service.py` - Business logic

## Docker Environment

**IMPORTANT**: This project is fully Dockerized. Always work within the Docker environment:

### Available Services
```yaml
services:
  api:      # Django application (port 8000)
  db:       # PostgreSQL 16 (port 5432)
  redis:    # Redis 7 (port 6379)
```

### Running Commands
```bash
# Run Django commands
docker compose exec api python manage.py <command>

# Run pytest
docker compose exec api python -m pytest <path> -v

# Install dependencies (after modifying requirements.txt)
docker compose down && docker compose up --build
```

### Database Migrations
```bash
# Create migrations
docker compose exec api python manage.py makemigrations

# Apply migrations
docker compose exec api python manage.py migrate
```

## Testing Requirements

**CRITICAL**: Every code change MUST include appropriate tests.

### Testing Stack
- **pytest** with `pytest-django` plugin
- **model-bakery** for generating test data
- Configuration in `api/pytest.ini`

### Test Requirements
1. **Always run tests** after creating or modifying code
2. **Create new tests** when adding features
3. **Update existing tests** when changing behavior
4. **Use fixtures** from `conftest.py` (don't duplicate setup)
5. **Aim for high coverage** - the accounts app has 92 tests

### Running Tests
```bash
# Run all tests
docker compose exec api python -m pytest apps/<app_name>/tests/ -v

# Run specific test file
docker compose exec api python -m pytest apps/<app_name>/tests/test_api.py -v

# Run with coverage
docker compose exec api python -m pytest apps/<app_name>/tests/ --cov=apps.<app_name> --cov-report=term-missing

# Run in quiet mode
docker compose exec api python -m pytest apps/<app_name>/tests/ -q --tb=no
```

### Test Organization
```python
# Always use pytest fixtures from conftest.py
@pytest.mark.django_db
class TestModelName:
    """Group related tests in classes"""
    
    def test_specific_behavior(self, fixture_name):
        """Use descriptive test names"""
        # Arrange
        data = baker.make(Model)
        
        # Act
        result = data.method()
        
        # Assert
        assert result == expected
```

### Test Coverage Guidelines
- **API endpoints**: Test success cases, error cases, authentication, permissions
- **Models**: Test creation, properties, methods, validation
- **Services**: Test business logic, edge cases, error handling
- **Schemas**: Test validation, default values, ModelSchema resolvers

## Django Ninja API Guidelines

### Endpoint Structure
```python
from ninja import Router
from .schemas import InputSchema, OutputSchema
from .auth import jwt_auth

router = Router(tags=['Category'])

@router.post('/endpoint', response={201: OutputSchema, 400: MessageSchema}, auth=jwt_auth)
def create_resource(request, payload: InputSchema):
    """
    Clear docstring describing the endpoint.
    """
    # Business logic in service layer
    result, error = service.create(payload)
    
    if error:
        return 400, {'message': error}
    
    return 201, result
```

### Schema Guidelines
1. **Use ModelSchema** when mapping directly from Django models
2. **Organize schemas by category** in separate files
3. **Use descriptive names**: `CreateUserSchema`, `UserResponseSchema`
4. **Include docstrings** for complex schemas
5. **Define resolvers** for computed fields in ModelSchema

```python
from ninja import ModelSchema

class UserSchema(ModelSchema):
    """User response schema with custom fields"""
    custom_field: str
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name']
    
    @staticmethod
    def resolve_custom_field(obj):
        return obj.compute_custom()
```

## Django Auditlog

**All models MUST be tracked** with django-auditlog for audit trail:

```python
from auditlog.registry import auditlog
from django.db import models

class YourModel(models.Model):
    # fields...
    pass

# Register for audit logging
auditlog.register(YourModel)
```

### What Gets Logged
- Model creation, updates, and deletions
- User who made the change (if authenticated)
- Timestamp of change
- Old and new values (diff)

## Code Quality Standards

### General Guidelines
1. **Follow PEP 8** style guide
2. **Use type hints** where beneficial
3. **Write docstrings** for classes and complex functions
4. **Keep functions focused** - single responsibility principle
5. **Use service layer** for business logic (don't put it in views/endpoints)

### Django Best Practices
1. **Never put business logic in API endpoints** - use services
2. **Use custom managers** for reusable query logic
3. **Use transactions** for multi-step database operations
4. **Validate at schema level** first, then in service layer
5. **Use select_related/prefetch_related** to avoid N+1 queries

### Security Practices
1. **Always validate user input** with schemas
2. **Use rate limiting** for sensitive endpoints (login, password reset)
3. **Never expose sensitive data** in error messages
4. **Use permissions** via custom auth classes
5. **Hash passwords** (never store plain text)

## Common Patterns

### Service Layer Pattern
```python
# services/resource_service.py
from typing import Tuple, Optional
from django.db import transaction

class ResourceService:
    def create_resource(self, data: dict) -> Tuple[Optional[Resource], Optional[str]]:
        """
        Create a new resource.
        
        Returns:
            Tuple of (resource, error_message)
        """
        try:
            with transaction.atomic():
                resource = Resource.objects.create(**data)
                # Additional logic
                return resource, None
        except Exception as e:
            return None, str(e)
```

### Test Fixture Pattern
```python
# tests/conftest.py
import pytest
from model_bakery import baker

@pytest.fixture
def sample_user(db):
    """Create a sample user for testing"""
    user = baker.make(User, email='test@example.com')
    user.set_password('testpass')
    user.save()
    return user

@pytest.fixture
def auth_headers(sample_user):
    """Get authentication headers for API tests"""
    refresh = RefreshToken.for_user(sample_user)
    return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
```

## Environment Variables

Key environment variables (defined in `compose.yml`):

```yaml
DATABASE_URL: PostgreSQL connection string
REDIS_URL: Redis connection string
SECRET_KEY: Django secret key
DEBUG: Debug mode (0/1)
ALLOWED_HOSTS: Comma-separated hosts
CORS_ALLOWED_ORIGINS: Frontend origins
```

## When Creating New Apps

1. **Create app in `api/apps/` directory**:
   ```bash
   docker compose exec api python manage.py startapp <app_name> apps/<app_name>
   ```

2. **Follow the standardized structure** (see above)

3. **Register in `INSTALLED_APPS`**:
   ```python
   # core/settings.py
   INSTALLED_APPS = [
       # ...
       '<app_name>',  # Note: no 'apps.' prefix due to sys.path configuration
   ]
   ```

4. **Register API router**:
   ```python
   # core/urls.py
   from <app_name>.api import router as <app_name>_router
   
   api.add_router('/<app_name>/', <app_name>_router)
   ```
   
   **Note**: The project uses `sys.path.insert(0, str(BASE_DIR / 'apps'))` in settings.py, which allows importing apps directly by name without the `apps.` prefix.

5. **Create comprehensive tests** from the start

6. **Register models with auditlog**

## Summary

When working on this project:
- ✅ **Use Django Ninja** for APIs (not DRF)
- ✅ **Follow the accounts app structure** as reference
- ✅ **Write tests for everything** - run them frequently
- ✅ **Use docker compose exec** for all commands
- ✅ **Organize schemas by category** in separate files
- ✅ **Use ModelSchema** when possible
- ✅ **Put business logic in services**
- ✅ **Register models with auditlog**
- ✅ **Use Django Groups** for permissions (not boolean flags)
- ✅ **Validate with pytest** before committing

The authentication system is fully implemented and battle-tested with 92 tests. Use it as a reference for building other app features.
