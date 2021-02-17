from . import views
from django.urls import path

# Namespace
app_name = 'projektadmin'

urlpatterns = [
    # Firmen-Verwaltung
    path('<projekt_id>/firma-anlegen/', views.firma_anlegen_view, name = 'firma_anlegen'),
    path('<projekt_id>/übersicht-firmen/', views.übersicht_firmen_view, name = 'übersicht_firmen'),
    path('<projekt_id>/freigabeverwaltung-ordner/<firma_id>/', views.freigabeverwaltung_ordner_view, name = 'freigabeverwaltung_ordner'),
    path('<projekt_id>/detailansicht-firma/<firma_id>', views.detailansicht_firma_view, name = 'detailansicht_firma'),

    # Ordner-Verwaltung
    path('<projekt_id>/übersicht-ordner/', views.übersicht_ordner_view, name = 'übersicht_ordner'),

    # WFSch-Verwaltung
    path('<projekt_id>/übersicht-wfsch/', views.übersicht_wfsch_view, name = 'übersicht_wfsch'),
    
    
]