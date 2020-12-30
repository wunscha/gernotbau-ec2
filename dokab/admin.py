from django.contrib import admin
from .models import Paket, Dokument, Status, Workflow, Workflow_Stufe, Mitarbeiter_Stufe_Status, Ereignis, Dokumentenhistorie_Eintrag, Anhang

admin.site.register(Paket)
admin.site.register(Dokument)
admin.site.register(Status)
admin.site.register(Workflow)
admin.site.register(Workflow_Stufe)
admin.site.register(Mitarbeiter_Stufe_Status)
admin.site.register(Ereignis)
admin.site.register(Dokumentenhistorie_Eintrag)
admin.site.register(Anhang)