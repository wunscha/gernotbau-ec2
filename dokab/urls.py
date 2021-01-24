from . import views
from django.urls import path
from django.http import HttpResponseRedirect

# Namespace
app_name = 'dokab'

urlpatterns = [
    # Anzeige Ordnerinhalt
    path('<projekt_id>/', views.übersicht_ordnerinhalt_root_view, name = 'übersicht_ordnerinhalt_root'),
    path('<projekt_id>/ordner/<ordner_id>/', views.übersicht_ordnerinhalt_view, name = 'übersicht_ordnerinhalt'),

    # Workflows
    path('<projekt_id>/workflows_übersicht/', views.workflows_übersicht, name = 'übersicht_wf'),
    path('<projekt_id>/workflow_detailansicht/<workflow_id>/', views.workflow_detailansicht, name = 'workflow_detailansicht'),

    # Dokumente
    path('<projekt_id>/upload/<ordner_id>/', views.upload, name = 'upload')
]