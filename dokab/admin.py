from django.contrib import admin
from .models import Dokument, Status, Workflow, Workflow_Stufe, Mitarbeiter_Stufe_Status, Anhang, Datei

admin.site.register(Dokument)
admin.site.register(Status)
admin.site.register(Workflow)
admin.site.register(Workflow_Stufe)
admin.site.register(Mitarbeiter_Stufe_Status)
admin.site.register(Anhang)
admin.site.register(Datei)