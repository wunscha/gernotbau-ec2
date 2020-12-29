from . import views
from django.urls import path
from django.http import HttpResponseRedirect

# Namespace
app_name = 'dokab'

urlpatterns = [
    # Anzeige Ordnerinhalt
    path('<projekt_id>/', views.weiterleitung_root, name = 'weiterleitung_root'),
    path('<projekt_id>/ordner/<ordner_id>/', views.ordner_inhalt, name = 'ordner_inhalt'),

    # Workflows
    path('<projekt_id>/', views.workflows_übersicht, name = 'workflows_übersicht')
]