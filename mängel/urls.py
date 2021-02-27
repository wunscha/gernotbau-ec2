from . import views
from django.urls import path

# Namespace
app_name = 'mängel'

urlpatterns = [
    path('<projekt_id>/übersicht-eingang/<filter>', views.übersicht_eingang_view, name = 'übersicht_eingang'),
    path('<projekt_id>/ticket-ausstellen/'), view.ticket_ausstellen, name = 'ticket_ausstellen',
    ]