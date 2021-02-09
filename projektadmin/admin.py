from django.contrib import admin
from .models import Workflow_Schema, WFSch_Stufe, Ordner, Ordner_Firma_Freigabe

admin.site.register(Workflow_Schema)
admin.site.register(WFSch_Stufe)
admin.site.register(Ordner)
admin.site.register(Ordner_Firma_Freigabe)