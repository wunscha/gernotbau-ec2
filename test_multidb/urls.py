from django.urls import path
from . import views

app_name = 'test_multidb'

urlpatterns= [
    path('<projekt_id>/', views.test_dokumente, name = 'test_dokumente'),
]