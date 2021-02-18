from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Firma, Projekt

EigenesUserModel = get_user_model()

admin.site.register(EigenesUserModel)
admin.site.register(Firma)
admin.site.register(Projekt)
