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
    path('<projekt_id>/workflows_übersicht/', views.workflows_übersicht, name = 'workflows_übersicht'),
    path('<projekt_id>/workflow_detailansicht/<workflow_id>/', views.workflow_detailansicht, name = 'workflow_detailansicht'),

    # Dokumente
    path('<projekt_id>/upload/<ordner_id>/', views.upload, name = 'upload')
]