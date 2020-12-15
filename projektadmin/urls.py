from . import views
from django.urls import path

urlpatterns = [
    # Workflow-Bearbeitung
    path('<projekt_id>/workflowschemata/',views.workflowschemataView, name='workflowschemata'),
    path('workflowschema_neu/', views.workflowschemaNeuView, name = 'workflowschema_neu'),
    path('wfschstufe_neu/', views.wfschStufeNeuView, name = 'wfschStufe_neu'),
    path('prüffirma_hinzufügen/', views.prüffirmaHinzufügenView, name = 'prüffirma_hinzufügen'),
    
    # Projektfirmen-Verwaltung
    path('<projekt_id>/firmen_übersicht/', views.firmenÜbersichtView, name = 'firmen_übersicht'),
    path('firma_hinzufügen/', views.firmaHinzufügenView, name = 'firma_hinzufügen'),
]