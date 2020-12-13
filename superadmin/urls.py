from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView
from . import views

urlpatterns = [
    path('firma_neu',views.firmaNeuView, name='firma_neu'),
    path('firma_neu',TemplateView.as_view(template_name='firma_neu_bestätigung.html'), name='firma_neu_bestätigung')
]