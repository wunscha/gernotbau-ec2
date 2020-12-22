from . import views
from django.urls import path

urlpatterns = [
    # Mitarbeiter-Bearbeitung
    path('',views.mitarbeiterÜbersichtView, name='firmenadmin_home'),
    path('mitarbeiter_übersicht/',views.mitarbeiterÜbersichtView, name='mitarbeiter_übersicht'),
    path('mitarbeiter_neu/', views.mitarbeiterNeuView, name = 'mitarbeiter_neu'),
    path('projekte_übersicht/',views.projekteÜbersichtView, name='projekte_übersicht'),
    path('workflows_übersicht/',views.workflowsÜbersichtView, name='workflows_übersicht'),
]