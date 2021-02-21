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
    path('<projekt_id>/übersicht_eigene_workflows/', views.übersicht_wf_eigene_dok_view, name = 'übersicht_wf_eigene_dok'),
    path('<projekt_id>/übersicht_wf_zur_bearbeitung/', views.übersicht_wf_zur_bearbeitung_view, name = 'übersicht_wf_zur_bearbeitung'),
    
    # Dokumente
    path('<projekt_id>/upload-dokument/<ordner_id>/', views.upload_dokument_view, name = 'upload_dokument'),
]