from django.db import models
from django.utils import timezone
from superadmin.models import Mitarbeiter
from projektadmin.models import Ordner, Workflow_Schema

'''
class Dokument(models.Model):
    bezeichnung = models.CharField(max_length = 50)
    pfad = models.CharField(max_length = 100)
    zeitstempel = models.DateTimeField()
    mitarbeiter_id = models.CharField(max_length=20, null = True) # TODO: nullable löschen (war nur für migrate-Befehl)
    ordner = models.ForeignKey(Ordner, on_delete = models.PROTECT)
    freigegeben = models.BooleanField(default = False)

    def __str__(self):
        return self.bezeichnung

class Datei(models.Model):
    dateiname = models.CharField(max_length = 50)
    pfad = models.CharField(max_length=100)
    dokument = models.ForeignKey(Dokument, on_delete=models.PROTECT)

    def __str__(self):
        return self.dateiname

class Status(models.Model):
    bezeichnung = models.CharField(max_length=20)
    
    def __str__(self):
        return self.bezeichnung

class Workflow(models.Model):
    dokument = models.OneToOneField(Dokument, on_delete = models.CASCADE)
    workflow_schema = models.ForeignKey(Workflow_Schema, on_delete = models.CASCADE)
    
    def __str__(self):
        return str('Workflow_%s' % self.dokument.bezeichnung)

class WF_Update_Abgeschlossen(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete = models.CASCADE)
    abgeschlossen = models.BooleanField()
    zeitstempel = models.DateTimeField()

    class Meta:
        ordering = ['zeitstempel']

class Workflow_Stufe(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete = models.CASCADE)
    vorstufe = models.ForeignKey('self', on_delete = models.CASCADE, null = True)
    bezeichnung = models.CharField(max_length = 20, default = 'Default')

    def __str__(self):
        return str('WF_Stufe_für_%s' % self.workflow)

class WF_Stufe_Update_Aktuell(models.Model):
    workflow_stufe = models.ForeignKey(Workflow_Stufe, on_delete = models.CASCADE, null = True) # TODO: nullable löschen
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

    class Meta:
        ordering = ['zeitstempel']

class Mitarbeiter_Stufe_Status(models.Model):
    mitarbeiter_id = models.CharField(max_length = 20, null = True) # TODO: nullable löschen (wurde nur für migration gebraucht)
    workflow_stufe = models.ForeignKey(Workflow_Stufe, on_delete = models.CASCADE)
    immer_erforderlich = models.BooleanField()
    
    def __str__(self):
        return str('%s-%s: %s' % (self.mitarbeiter.last_name, self.workflow_stufe, self.status))

class MA_Stufe_Status_Update_Status(models.Model):
    ma_stufe_status = models.ForeignKey(Mitarbeiter_Stufe_Status, on_delete = models.CASCADE)
    status = models.ForeignKey(Status, on_delete = models.PROTECT)
    zeitstempel = models.DateTimeField()

    class Meta:
        ordering = ['zeitstempel']

class Statuskommentar(models.Model):
    ma_stufe_status_update_status = models.OneToOneField(MA_Stufe_Status_Update_Status, on_delete = models.CASCADE)
    text = models.CharField(max_length = 100)

class Anhang(models.Model):
    bezeichnung = models.CharField(max_length = 50)
    pfad = models.CharField(max_length = 100)

    def __str__(self):
        return self.bezeichnung
'''