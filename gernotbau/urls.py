"""gernotbau URL Configuration

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
from django.urls import path, include
from django.views.generic.base import TemplateView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Weiterleitung zum Usermanagement
    path('accounts/', include('django.contrib.auth.urls')),

    # Weiterleitung zu Superadmin
    path('superadmin/', include('superadmin.urls')),

    # Weiterleitung zu Projektadmin
    path('projektadmin/', include('projektadmin.urls')),

    # Weiterleitung zu Firmenadmin
    path('firmenadmin/', include('firmenadmin.urls')),

    # Weiterleitung zu DokAb
    path('dokab/', include('dokab.urls')),

    # Weiterleitung zu Test MultiDB
    path('test_multidb/', include('test_multidb.urls')),

    # Home
    path('', views.home_view, name='home'),

    # Login-Formular
    path('login/', views.login_view, name = 'login'),
]
