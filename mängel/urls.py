from . import views
from django.urls import path

# Namespace
app_name = 'mängel'

urlpatterns = [
    path('<projekt_id>/übersicht-tickets/', views.übersicht_tickets_view, name = 'übersicht_tickets'),
    path('<projekt_id>/ticket-ausstellen/', views.ticket_ausstellen_view, name = 'ticket_ausstellen'),
    path('<projekt_id>/detailansicht-ticket/<ticket_id>/', views.detailansicht_ticket_view, name = 'detailansicht_ticket'),
    path('<projekt_id>/übersicht-pläne/', views.übersicht_pläne_view, name = 'übersicht_pläne'),
    path('<projekt_id>/plan-anlegen/', views.plan_anlegen_view, name = 'plan_anlegen'),
    ]