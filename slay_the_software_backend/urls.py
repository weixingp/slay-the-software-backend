"""slay_the_software_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from main.admin import custom_admin_site
from django.urls import path, include
from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets

from main import views
from main.urls import urlpatterns as main_urls

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

urlpatterns = [
    path('', include(router.urls)),
    #path('admin/', admin.site.urls),
    path('admin/', custom_admin_site.urls),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('share/', views.assignment_share_page),
    path('share/challenge/', views.challenge_share_page),
]

# API account url
api_account = [
    path('api/account/login/', views.LoginView.as_view()),
    path('api/account/logout/', views.LogoutView.as_view()),
    path('api/account/create/', views.RegisterView.as_view()),
    path('api/account/changepassword/', views.ChangePasswordView.as_view()),
]
urlpatterns += api_account
urlpatterns += main_urls
