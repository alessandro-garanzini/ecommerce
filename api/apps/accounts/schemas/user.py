from ninja import ModelSchema
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSchema(ModelSchema):
    """User schema using ModelSchema for automatic field mapping"""
    is_customer: bool
    role: str
    groups: list[str]
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined']
    
    @staticmethod
    def resolve_is_customer(obj):
        return obj.is_customer
    
    @staticmethod
    def resolve_role(obj):
        return obj.get_role_display()
    
    @staticmethod
    def resolve_groups(obj):
        return list(obj.groups.values_list('name', flat=True))
