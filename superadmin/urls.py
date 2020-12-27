from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView
from . import views

# Namespace
app_name = 'superadmin'

urlpatterns = [
    path('firma_neu/',views.firmaNeuView, name='firma_neu'),
    path('projekt_neu/',views.projektNeuView, name='projekt_neu'),
     # Weiterleitung zur Heimseite
    path('', views.homeView, name='home')
]