from django.urls import path
from . import views

app_name = 'vorlagen'

urlpatterns= [
    path('<db_bezeichnung>', views.test_ordner_view, name = 'test_ordner'),
]