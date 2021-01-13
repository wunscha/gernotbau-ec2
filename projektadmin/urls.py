from . import views
from django.urls import path

# Namespace
app_name = 'projektadmin'

urlpatterns = [
    # Workflow-Bearbeitung
    path('<projekt_id>/workflowschemata/',views.workflowschemataView, name='workflowschemata'),
    path('workflowschema_neu/', views.workflowschemaNeuView, name = 'workflowschema_neu'),
    path('wfschstufe_neu/', views.wfschStufeNeuView, name = 'wfschStufe_neu'),
    path('prüffirma_hinzufügen/', views.prüffirmaHinzufügenView, name = 'prüffirma_hinzufügen'),
    
    # Projektfirmen-Verwaltung
    path('<projekt_id>/übersicht_firmen/', views.übersicht_firmen_view, name = 'übersicht_firmen'),
    path('<projekt_id>/firma_detail/<firma_id>/', views.firmaDetailView, name = 'firma_detail'),
    path('<projekt_id>/ordner_freigabe_ändern/<firma_id>/', views.ordner_freigabe_ändern, name = 'ordner_freigabe_ändern'),

    # Ordner-Verwaltung
    path('<projekt_id>/ordner_übersicht/', views.ordnerÜbersichtView, name = 'ordner_übersicht'),
    path('<überordner_id>/ordner_neu/', views.ordnerNeuView, name = 'ordner_neu'),
    path('wfsch_ändern', views.wfschÄndernView, name = 'wfsch_ändern')
]