from django import db
from django.db import models
from django.contrib.auth.models import AbstractUser

class Firma(models.Model):
    bezeichnung = models.CharField(max_length=50)
    kurzbezeichnung = models.CharField(max_length=10)
    strasse = models.CharField(max_length=50, null=True)
    hausnummer = models.CharField(max_length=50, null=True)
    postleitzahl = models.CharField(max_length = 10)
    ort = models.CharField(max_length=50)
    email_office = models.EmailField()
    email = models.EmailField()
    aktiv = models.BooleanField(default = True)

    def __str__(self):
        return self.kurzbezeichnung

    ############
    # Neue Herangehensweise (Funktionen in models definieren): 06.02.2021

    def liste_rollen(self, db_bezeichnung):
    # Gibt Liste der aktuellen Rollen von Firma zurück
        li_rollen = []
        for e in projektadmin.Rolle_Firma.objects.using(db_bezeichnung).filter(firma_id = self.id):
            if e.aktuell(db_bezeichnung): li_rollen.append(e.rolle)
        return li_rollen

    def freigaben_rollen_übernehmen(self, db_bezeichnung):
    # Überträgt alle Ordnerfreigaben der zugewiesenen Rollen auf Firma
        projekt = Projekt.objects.using('default').get(db_bezeichnung = db_bezeichnung)
        li_rollen = self.liste_rollen(db_bezeichnung)
        for r in li_rollen:
            for o in projekt.liste_ordner():
                # Freigaben zurücksetzen
                o.lesefreigabe_entziehen(db_bezeichnung, self)
                o.uploadfreigabe_entziehen(db_bezeichnung, self)
                # Freigaben übernehmen
                if o.freigabe_lesen_rolle(db_bezeichnung, r): o.lesefreigabe_erteilen_firma(db_bezeichnung, self)
                if o.freigabe_upload_rolle(db_bezeichnung, r): o.uploadfreigabe_erteilen_firma(db_bezeichnung, self)

class Mitarbeiter(AbstractUser):
    firma = models.ForeignKey(
        'Firma', 
        on_delete=models.CASCADE,
        null = True)
    ist_firmenadmin = models.BooleanField(default = False)
    ist_superadmin = models.BooleanField(default = False)
    aktiv = models.BooleanField(default = True)

    def __str__(self):
        return self.username

class Projekt(models.Model):
    bezeichnung = models.CharField(max_length=50)
    kurzbezeichnung = models.CharField(max_length=10)
    mitarbeiter = models.ManyToManyField(
        'Mitarbeiter',
        through = 'Projekt_Mitarbeiter_Mail',
        through_fields = ('projekt', 'mitarbeiter'),
    )
    firma = models.ManyToManyField(
        Firma,
        through = 'Projekt_Firma_Mail',
        through_fields = ('projekt', 'firma'),
    )
    aktiv = models.BooleanField(default = True)
    db_bezeichnung = models.CharField(max_length = 25, default = 'pj_projektID')

    def __str__(self):
        return self.kurzbezeichnung

    ############
    # Neue Herangehensweise (Funktionen in models definieren): 06.02.2021

    def liste_ordner(self): # TODO: db_bezeichnung soll in 
    # Gibt Liste aller nicht gelöschten Ordner zurück
        li_ordner = []
        for o in projektadmin.Ordner.objects.using(self.db_bezeichnung).all():
            if not o.gelöscht(self.db_bezeichnung): 
                li_ordner.append(o)
        return li_ordner

class Projekt_Mitarbeiter_Mail(models.Model):
    ist_projektadmin = models.BooleanField()
    email = models.EmailField()
    projekt = models.ForeignKey('Projekt', on_delete = models.CASCADE)
    mitarbeiter = models.ForeignKey('Mitarbeiter', on_delete = models.CASCADE)

    def __str__(self):
        return str('%s - %s, %s' % (self.projekt.kurzbezeichnung, self.mitarbeiter.last_name, self.mitarbeiter.first_name,))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ['projekt', 'mitarbeiter'], name = 'verbindung_pj-ma_unique'), # Verbindung Projekt-Mitarbeiter soll unique sein
        ]

class Projekt_Firma_Mail(models.Model):
    ist_projektadmin = models.BooleanField()
    email = models.EmailField()
    projekt = models.ForeignKey('Projekt', on_delete = models.CASCADE)
    firma = models.ForeignKey('Firma', on_delete = models.CASCADE)

    def __str__(self):
        return str(self.projekt.kurzbezeichnung + '-' + self.firma.kurzbezeichnung)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ['projekt', 'firma'], name = 'verbindung_pj-fa_unique') # Verbindung Projekt-Firma soll unique sein
        ]