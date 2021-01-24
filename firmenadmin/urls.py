from . import views
from django.urls import path

# Namespace
app_name = 'firmenadmin'

urlpatterns = [
    # Mitarbeiter
    path('übersicht_mitarbeiter/',views.übersicht_mitarbeiter_view, name='übersicht_mitarbeiter'),
    path('mitarbeiter_neu/', views.mitarbeiter_neu_view, name = 'mitarbeiter_neu'),
    
    # Projekte
    path('übersicht_projekte/',views.übersicht_projekte_view, name='übersicht_projekte'),
    
    # Workflows
    path('übersicht_wfsch/',views.übersicht_wfsch_view, name='übersicht_wfsch'),
]