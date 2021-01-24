from django.db import models
from superadmin.models import Mitarbeiter
from projektadmin.models import Ordner, Workflow_Schema

class Dokument(models.Model):
    bezeichnung = models.CharField(max_length = 50)
    pfad = models.CharField(max_length = 100)
    zeitstempel = models.DateTimeField()
    mitarbeiter_id = models.CharField(max_length=20, null = True) # TODO: nullable löschen (war nur für migrate-Befehl)
    ordner = models.ForeignKey(Ordner, on_delete = models.PROTECT)

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
    status = models.ForeignKey(Status, on_delete = models.PROTECT)
    abgeschlossen = models.BooleanField()

    def __str__(self):
        return str('Workflow_%s' % self.dokument.bezeichnung)

class Workflow_Stufe(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete = models.CASCADE)
    vorstufe = models.ForeignKey('self', on_delete = models.CASCADE, null = True)
    aktuell = models.BooleanField(default = False)
    
    def __str__(self):
        return str('WF_Stufe_für_%s' % self.workflow)

class Mitarbeiter_Stufe_Status(models.Model):
    mitarbeiter_id = models.CharField(max_length = 20, null = True) # TODO: nullable löschen (wurde nur für migration gebraucht)
    workflow_stufe = models.ForeignKey(Workflow_Stufe, on_delete = models.CASCADE)
    status = models.ForeignKey(Status, on_delete = models.PROTECT)
    immer_erforderlich = models.BooleanField()

    def __str__(self):
        return str('%s-%s: %s' % (self.mitarbeiter.last_name, self.workflow_stufe, self.status))

class Firma_Stufe(models.Model):
    firma_id = models.CharField(max_length=20)
    workflow_stufe = models.ForeignKey(Workflow_Stufe, on_delete = models.CASCADE)
    
    def __str__(self):
        return str('firmen_id: %s - wf_stufe_id: %s' % (self.firma_id, self.workflow_stufe.id))

class Ereignis(models.Model):
    bezeichnung = models.CharField(max_length = 20)

    def __str__(self):
        return self.bezeichnung

class Dokumentenhistorie_Eintrag(models.Model):
    text = models.CharField(max_length = 200)
    zeitstempel = models.DateTimeField()
    dokument = models.ForeignKey(Dokument, on_delete = models.CASCADE)
    ereignis = models.ForeignKey(Ereignis, on_delete = models.PROTECT)
    mitarbeiter_id = models.CharField(max_length=20, null = True) # TODO: nullable entfernen (war für migration-Befehl notwendig)

    def __str__(self):
        return str('%s - %s' % (self.zeitstempel, self.ereignis))

class Anhang(models.Model):
    bezeichnung = models.CharField(max_length = 50)
    pfad = models.CharField(max_length = 100)
    dokumentenhistorie_eintrag = models.ForeignKey(Dokumentenhistorie_Eintrag, on_delete = models.CASCADE)

    def __str__(self):
        return self.bezeichnung