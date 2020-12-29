from . import views
from django.urls import path

# Namespace
app_name = 'firmenadmin'

urlpatterns = [
    # Mitarbeiter
    path('',views.mitarbeiterÜbersichtView, name='firmenadmin_home'),
    path('mitarbeiter_übersicht/',views.mitarbeiterÜbersichtView, name='mitarbeiter_übersicht'),
    path('mitarbeiter_neu/', views.mitarbeiterNeuView, name = 'mitarbeiter_neu'),
    
    # Projekte
    path('projekte_übersicht/',views.projekteÜbersichtView, name='projekte_übersicht'),
    path('mitarbeiter_zu_projekt/',views.mitarbeiter_zu_projekt, name='mitarbeiter_zu_projekt'),
    path('mitarbeiter_als_projektadmin/',views.mitarbeiter_als_projektadmin, name='mitarbeiter_als_projektadmin'),
 
    # Workflows
    path('workflows_übersicht/',views.workflowsÜbersichtView, name='workflows_übersicht'),
    path('wfsch_prüfer_zuordnen/',views.wfsch_prüfer_zuordnen, name='wfsch_prüfer_zuordnen')
]