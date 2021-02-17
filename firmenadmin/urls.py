from . import views
from django.urls import path

# Namespace
app_name = 'firmenadmin'

urlpatterns = [
    # Mitarbeiter
    path('<firma_id>/übersicht_mitarbeiter/',views.übersicht_mitarbeiter_view, name='übersicht_mitarbeiter'),
    path('<firma_id>/mitarbeiter_anlegen/', views.mitarbeiter_anlegen_view, name = 'mitarbeiter_anlegen'),
    
    # Projekte
    path('<firma_id>/übersicht_projekte/',views.übersicht_projekte_view, name='übersicht_projekte'),
    
    # Workflows
    path('übersicht_wfsch/',views.übersicht_wfsch_view, name='übersicht_wfsch'),
]