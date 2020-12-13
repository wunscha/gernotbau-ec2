from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Firma, Projekt, Projekt_Firma_Mail, Projekt_Mitarbeiter_Mail

EigenesUserModel = get_user_model()

admin.site.register(EigenesUserModel)
admin.site.register(Firma)
admin.site.register(Projekt)
admin.site.register(Projekt_Firma_Mail)
admin.site.register(Projekt_Mitarbeiter_Mail)

# Register your models here.
