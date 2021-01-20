from django.contrib import admin
from .models import Workflow_Schema, Workflow_Schema_Stufe, Ordner, Ordner_Firma_Freigabe, Überordner_Unterordner

admin.site.register(Workflow_Schema)
admin.site.register(Workflow_Schema_Stufe)
admin.site.register(Ordner)
admin.site.register(Ordner_Firma_Freigabe)
admin.site.register(Überordner_Unterordner)