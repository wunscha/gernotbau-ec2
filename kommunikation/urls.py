from . import views
from django.urls import path

# Namespace
app_name = 'kommunikation'

urlpatterns = [
    path('übersicht-eingang/', views.übersicht_eingang_view, name = 'übersicht_eingang'),
    path('übersicht-gesendet/', views.übersicht_gesendet_view, name = 'übersicht_gesendet'),
    path('detailansicht-nachricht/<nachricht_id>', views.detailansicht_nachricht_view, name = 'detailansicht_nachricht'),
    path('nachricht-verfassen/<empfänger_id>', views.nachricht_verfassen_view, name = 'nachricht_verfassen')
    ]