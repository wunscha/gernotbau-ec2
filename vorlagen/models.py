from django.db import models
from django.db.models.fields import DateTimeField

# Create your models here.

class V_Ordner(models.Model):
    zeitstempel = models.DateTimeField()
    ist_root_ordner = models.BooleanField()

    def bezeichnung(self, projekt):
        return V_Ordner_Bezeichnung.objects.using(str(projekt.id)).filter(v_ordner = self).latest('zeitstempel').bezeichnung

    def freigabe_lesen(self, projekt, v_rolle):
        v_ordner_rolle = V_Ordner_Rolle.objects.using(str(projekt.id)).get(v_ordner = self, v_rolle = v_rolle)
        return V_Ordner_Freigabe_Lesen.objects.using(str(projekt.id)).filter(v_ordner_rolle = v_ordner_rolle).latest('zeitstempel').freigabe_lesen

class V_Order_Update_Unterordner(models.Model):
    v_überordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE, related_name = 'v_überordner')
    v_unterordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE, related_name = 'v_unterordner')
    zeitstempel = models.DateTimeField()

class V_Ordner_Update_Unterordner_aktuell(models.Model):
    v_unterordner = models.ForeignKey(V_Order_Update_Unterordner, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_Workflow_Schema(models.Model):
    zeitstempel = models.DateTimeField()

class V_Ordner_Bezeichnung(models.Model):
    v_ordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField()

class V_Rolle(models.Model):
    zeitstempel = models.DateTimeField()

    def bezeichnung(self, projekt):
        return V_Rolle_Bezeichnung.objects.using(str(projekt.id)).filter(v_rolle = self).latest('zeitstempel').bezeichnung

class V_Rolle_Bezeichnung(models.Model):
    v_rolle = models.ForeignKey(V_Rolle, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField

class V_Ordner_Rolle(models.Model):
    v_ordner = models.ForeignKey(V_Ordner, on_delete = models.CASCADE)
    v_rolle = models.ForeignKey(V_Rolle, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

class V_Ordner_Freigabe_Lesen(models.Model):
    v_ordner_rolle = models.ForeignKey(V_Ordner_Rolle, on_delete = models.CASCADE)
    freigabe_lesen = models.BooleanField()
    zeitstempel = models.DateTimeField()

class V_Ordner_Freigabe_Upload(models.Model):
    v_ordner_rolle = models.ForeignKey(V_Ordner_Rolle, on_delete = models.CASCADE)
    freigabe_upload = models.BooleanField()
    zeitstempel = models.DateTimeField()