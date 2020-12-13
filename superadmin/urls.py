from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView
from . import views

urlpatterns = [
    path('firma_neu/',views.firmaNeuView, name='firma_neu'),
    path('projekt_neu/',views.projektNeuView, name='projekt_neu'),
]