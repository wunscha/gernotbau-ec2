from . import views
from django.urls import path

# Namespace
app_name = 'projektadmin'

urlpatterns = [
    # Workflow-Bearbeitung
    path('<projekt_id>/workflowschemata/',views.übersicht_workflowschemata, name='übersicht_workflowschemata'),
    
    # Projektfirmen-Verwaltung
    path('<projekt_id>/übersicht_firmen/', views.übersicht_firmen_view, name = 'übersicht_firmen'),
    path('<projekt_id>/freigabeverwaltung_ordner/<firma_id>/', views.freigabeverwaltung_ordner, name = 'freigabeverwaltung_ordner'),

    # Ordner-Verwaltung
    path('<projekt_id>/übersicht_ordner/', views.übersicht_ordner_view, name = 'übersicht_ordner'),

    # Test
    path('<projekt_id>/übersicht-wfsch/', views.übersicht_wfsch, name = 'übersicht_wfsch'),
    path('<projekt_id>/firma-neu/', views.firma_neu_view, name = 'firma_neu'),
]