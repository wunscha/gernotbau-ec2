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

    # Ordner-Verwaltung
    path('<projekt_id>/ordner_übersicht/', views.ordnerÜbersichtView, name = 'ordner_übersicht'),
    path('ordner_neu/', views.ordnerNeuView, name = 'ordner_neu'),
    path('wfsch_ändern', views.wfschÄndernView, name = 'wfsch_ändern')
]