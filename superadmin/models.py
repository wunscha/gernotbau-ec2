from django import db
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.fields import BooleanField, DateTimeField
from django.db.models.fields.related import ForeignKey
from django.utils import timezone

class Firma(models.Model):
    # bezeichnung = models.CharField(max_length=50) # TODO: Feld löschen
    # kurzbezeichnung = models.CharField(max_length=10) # TODO: Feld löschen
    # strasse = models.CharField(max_length=50, null=True) # TODO: Feld löschen
    # hausnummer = models.CharField(max_length=50, null=True) # TODO: Feld löschen
    # postleitzahl = models.CharField(max_length = 10) # TODO: Feld löschen
    # ort = models.CharField(max_length=50) # TODO: Feld löschen
    # email_office = models.EmailField() # TODO: Feld löschen
    # email = models.EmailField() # TODO: Feld löschen
    # aktiv = models.BooleanField(default = True) # TODO: Feld löschen
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable löschen

    def __str__(self):
        return self.kurzbezeichnung

    # FIRMA GELÖSCHT
    def löschen(self, db_bezeichnung):
        Firma_Gelöscht.objects.using(db_bezeichnung).create(
            firma = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def entlöschen(self, db_bezeichnung):
        Firma_Gelöscht.objects.using(db_bezeichnung).create(
            firma = self,
            gelöscht = False,
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        return Firma_Gelöscht.objects.using(db_bezeichnung).filter(firma = self).latest('zeitstempel').gelöscht

    # FIRMA ROLLEN
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

    # FIRMA BEZEICHNUNG
    def bezeichnung_ändern(self, db_bezeichnung, neue_bezeichnung):
        Firma_Bezeichnung.objects.using(db_bezeichnung).create(
            firma = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, db_bezeichnung):
        return Firma_Bezeichnung.objects.using(db_bezeichnung).filter(firma = self).latest('zeitstempel').bezeichnung

    # FIRMA KURZBEZEICHNUNG
    def kurzbezeichnung_ändern(self, db_bezeichnung, neue_kurzbezeichnung):
        Firma_Kurzbezeichnung.objects.using(db_bezeichnung).create(
            firma = self,
            kurzbezeichnung = neue_kurzbezeichnung,
            zeitstempel = timezone.now()
            )

    def kurzbezeichnung(self, db_bezeichnung):
        return Firma_Kurzbezeichnung.objects.using(db_bezeichnung).filter(firma = self).latest('zeitstempel').kurzbezeichnung

    # FIRMA STRASSE
    def strasse_ändern(self, db_bezeichnung, neue_strasse):
        Firma_Strasse.objects.using(db_bezeichnung).create(
            firma = self,
            strasse = neue_strasse,
            zeitstempel = timezone.now()
            )
    
    def strasse(self, db_bezeichnung):
        return Firma_Strasse.objects.using(db_bezeichnung).filter(firma = self).latest('zeitstempel').strasse

    # FIRMA HAUSNUMMER
    def hausnummer_ändern(self, db_bezeichnung, neue_hausnummer):
        Firma_Hausnummer.objects.using(db_bezeichnung).create(
            firma = self,
            hausnummer = neue_hausnummer,
            zeitstempel = timezone.now()
            )

    def hausnummer(self, db_bezeichnung):
        return Firma_Hausnummer.objects.filter(firma = self).latest('zeitstempel').hausnummer

    # FIRMA POSTLEITZAHL
    def postleitzahl_ändern(self, db_bezeichnung, neue_postleitzahl):
        Firma_Postleitzahl.objects.using(db_bezeichnung).create(
            firma = self,
            postleitzahl = neue_postleitzahl,
            zeitstempel = timezone.now()
            )

    def postleitzahl(self, db_bezeichnung):
        return Firma_Postleitzahl.objects.using(db_bezeichnung).filter(firma = self).latest('zeitstempel').postleitzahl

    # FIRMA ORT
    def ort_ändern(self, db_bezeichnung, neuer_ort):
        Firma_Ort.objects.using(db_bezeichnung).create(
            firma = self, 
            ort = neuer_ort,
            zeitstempel = timezone.now()
            )

    def ort(self, db_bezeichnung):
        return Firma_Ort.objects.using(db_bezeichnung).filter(firma = self).latest('zeitstempel').ort

    # FIRMA EMAIL
    def email_ändern(self, db_bezeichnung, neue_email):
        Firma_Email.objects.using(db_bezeichnung).create(
            firma = self,
            email = neue_email,
            zeitstempel = timezone.now()
            )
    
    def email(self, db_bezeichnung):
        return Firma_Email.objects.using(db_bezeichnung).filter(firma = self).latest('zeitstempel').email

    # FIRMA DICT
    def firma_dict(self, db_bezeichnung):
        fa_dict = self.__dict__
        fa_dict['bezeichnung'] = self.bezeichnung(db_bezeichnung)
        # fa_dict['kurzbezeichnung'] = self.kurzbezeichnung(db_bezeichnung)
        # fa_dict['strasse'] = self.strasse(db_bezeichnung)
        # fa_dict['hausnummer'] = self.hausnummer(db_bezeichnung)
        # fa_dict['postleitzahl'] = self.postleitzahl(db_bezeichnung)
        # fa_dict['ort'] = self.ort(db_bezeichnung)
        # fa_dict['email'] = self.email(db_bezeichnung)
        return fa_dict

class Firma_Bezeichnung(models.Model):
    firma = models.ForeignKey(Firma, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField()

class Firma_Kurzbezeichnung(models.Model):
    firma = models.ForeignKey(Firma, on_delete = models.CASCADE)
    kurzbezeichnung = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField()

class Firma_Strasse(models.Model):
    firma = models.ForeignKey(Firma, on_delete = models.CASCADE)
    strasse = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable entfernen

class Firma_Hausnummer(models.Model):
    firma = models.ForeignKey(Firma, on_delete = models.CASCADE)
    hausnummer = models.CharField(max_length = 10)
    zeitstempel = models.DateTimeField()

class Firma_Postleitzahl(models.Model):
    firma = models.ForeignKey(Firma, on_delete = models.CASCADE)
    postleitzahl = models.CharField(max_length = 15)
    zeitstempel = models.DateTimeField()

class Firma_Ort(models.Model):
    firma = models.ForeignKey(Firma, on_delete = models.CASCADE)
    ort = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField()

class Firma_Email(models.Model):
    firma = models.ForeignKey(Firma, on_delete = models.CASCADE)
    email = models.EmailField()
    zeitstempel = timezone.now()

class Firma_Gelöscht(models.Model):
    firma = models.ForeignKey(Firma, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

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
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable entfernen

    # PROJEKT GELÖSCHT
    def löschen(self, db_bezeichnung):
        Projekt_Gelöscht.objects.using(db_bezeichnung).create(
            projekt = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )
        
    def entlöschen(self, db_bezeichnung):
        Projekt_Gelöscht.objects.using(db_bezeichnung).create(
            projekt = self,
            gelöscht = False,
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        Projekt_Gelöscht.objects.using(db_bezeichnung).filter(projekt = self).latest('zeitstempel').gelöscht

    # PROJEKT BEZEICHNUNG
    def bezeichnung_ändern(self, db_bezeichnung, neue_bezeichnung):
        Projekt_Bezeichnung.objects.using(db_bezeichnung).create(
            projekt = self,
            bezeichnung = neue_bezeichnung, 
            zeitstempel = timezone.now()
            )

    def bezeichnung(self, db_bezeichnung):
        return Projekt_Bezeichnung.objects.using(db_bezeichnung).filter(projekt = self).latest('zeitstempel').bezeichnung

    # PROJEKT KURZBEZEICHNUNG
    def kurzbezeichnung_ändern(self, db_bezeichnung, neue_kurzbezeichnung):
        Projekt_Kurzbezeichnung.objects.using(db_bezeichnung).create(
            projekt = self,
            kurzbezeichnung = neue_kurzbezeichnung,
            zeitstempel = timezone.now()
            )

    def kurzbezeichnung(self, db_bezeichnung):
        return Projekt_Kurzbezeichnung.objects.using(db_bezeichnung).filter(projekt = self).latest('zeitstempel').kurzbezeichnung

    # PROJEKT LISTE FIRMEN
    def liste_firmen(self, db_bezeichnung):
        li_firmen = []
        for verbindung_pj_fa in Projekt_Firma.objects.using(db_bezeichnung).filter(projekt = self):
            if verbindung_pj_fa.aktuell(db_bezeichnung) and not verbindung_pj_fa.firma.gelöscht(db_bezeichnung):
                li_firmen.append(verbindung_pj_fa.firma)
        return li_firmen

    # PROJEKT DB_BEZEICHNUNG
    def db_bezeichnung(self, db_bezeichnung):
        return Projekt_DB.objects.using(db_bezeichnung).filter(projekt = self).latest('zeitstempel').db_bezeichnung

class Projekt_DB(models.Model):
    projekt = models.ForeignKey(Projekt, on_delete = models.CASCADE)
    db_bezeichnung = models.CharField(max_length = 50)
    zeitstempel = models.DateTimeField()

class Projekt_Gelöscht(models.Model):
    projekt = models.ForeignKey(Projekt, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Projekt_Bezeichnung(models.Model):
    projekt = models.ForeignKey(Projekt, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 20)
    zeitstempel = models.DateTimeField()

class Projekt_Kurzbezeichnung(models.Model):
    projekt = models.ForeignKey(Projekt, on_delete = models.CASCADE)
    kurzbezeichnung = models.CharField(max_length = 20)
    zeitstempel = models.DateTimeField()

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

class Projekt_Firma(models.Model):
    projekt = models.ForeignKey('Projekt', on_delete = models.CASCADE)
    firma = models.ForeignKey('Firma', on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField(null = True) # Nullable entfernen

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ['projekt', 'firma'], name = 'verbindung_pj-fa_unique') # Verbindung Projekt-Firma soll unique sein
        ]

    # PROJEKT_FIRMA AKTUELL
    def aktualisieren(self, db_bezeichnung):
        Projekt_Firma_Aktuell.objects.using(db_bezeichnung).create(
            projekt_firma = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self, db_bezeichnung):
        Projekt_Firma_Aktuell.objects.using(db_bezeichnung).create(
            projekt_firma = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self, db_bezeichnung):
        return Projekt_Firma_Aktuell.objects.using(db_bezeichnung).filter(projekt_firma = self).latest('zeitstempel').aktuell

class Projekt_Firma_Aktuell(models.Model):
    projekt_firma = models.ForeignKey(Projekt_Firma, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()