from . import views
from django.urls import path

# Namespace
app_name = 'firmenadmin'

urlpatterns = [
    # Mitarbeiter
    path('<firma_id>/übersicht-mitarbeiter/', views.übersicht_mitarbeiter_view, name='übersicht_mitarbeiter'),
    path('<firma_id>/detailansicht-mitarbeiter/<mitarbeiter_id>/', views.detailansicht_mitarbeiter_view, name='detailansicht_mitarbeiter'),
    path('<firma_id>/mitarbeiter-anlegen/', views.mitarbeiter_anlegen_view, name = 'mitarbeiter_anlegen'),
    
    # Projekte
    path('<firma_id>/übersicht-projekte/',views.übersicht_projekte_view, name='übersicht_projekte'),
    
    # Workflows
    path('<firma_id>/übersicht-wfsch/',views.übersicht_wfsch_view, name='übersicht_wfsch'),
]