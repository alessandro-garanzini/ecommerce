"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from accounts.api import router as auth_router

api = NinjaAPI(
    title='Ecommerce API',
    version='1.0.0',
    description='Ecommerce backend API with JWT authentication'
)

# Register routers
api.add_router('/auth/', auth_router)

# Test endpoint
@api.get("/health")
def health_check(request):
    return {"status": "healthy", "message": "API is running"}

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", api.urls),
]
