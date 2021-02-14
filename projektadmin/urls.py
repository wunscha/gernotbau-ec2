from . import views
from django.urls import path

# Namespace
app_name = 'projektadmin'

urlpatterns = [
    # Workflow-Bearbeitung
    path('<projekt_id>/workflowschemata/',views.übersicht_workflowschemata, name='übersicht_workflowschemata'),
    
    # Projektfirmen-Verwaltung
    path('<projekt_id>/übersicht-firmen/', views.übersicht_firmen_view, name = 'übersicht_firmen'),
    path('<projekt_id>/freigabeverwaltung-ordner/<firma_id>/', views.freigabeverwaltung_ordner_view, name = 'freigabeverwaltung_ordner'),

    # Ordner-Verwaltung
    path('<projekt_id>/übersicht_ordner/', views.übersicht_ordner_view, name = 'übersicht_ordner'),

    # Test
    path('<projekt_id>/übersicht-wfsch/', views.übersicht_wfsch_view, name = 'übersicht_wfsch'),
    path('<projekt_id>/firma-anlegen/', views.firma_anlegen_view, name = 'firma_anlegen'),
    path('<projekt_id>/detailansict-firma/<firma_id>', views.detailansicht_firma_view, name = 'detailansicht_firma')
]