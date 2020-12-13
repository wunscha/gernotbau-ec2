from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Firma

EigenesUserModel = get_user_model()

admin.site.register(EigenesUserModel)
admin.site.register(Firma)

# Register your models here.
