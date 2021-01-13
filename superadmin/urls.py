from django.urls import path
from . import views

# Namespace
app_name = 'superadmin'

urlpatterns = [
    path('', views.firma_neu_view, name='superadmin_home'),
    path('firma_neu/',views.firma_neu_view, name='firma_neu'),
    path('projekt_neu/',views.projekt_neu_view, name='projekt_neu'),
]