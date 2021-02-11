from django import db
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.fields import BooleanField, DateTimeField
from django.db.models.fields.related import ForeignKey
from django.utils import timezone

class Firma(models.Model):
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable löschen

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
        qs_fa_kurzbezeichnung = Firma_Kurzbezeichnung.objects.using(db_bezeichnung).filter(firma = self)
        if qs_fa_kurzbezeichnung:
            return qs_fa_kurzbezeichnung.latest('zeitstempel').kurzbezeichnung
        else:
            return None

    # FIRMA STRASSE
    def strasse_ändern(self, db_bezeichnung, neue_strasse):
        Firma_Strasse.objects.using(db_bezeichnung).create(
            firma = self,
            strasse = neue_strasse,
            zeitstempel = timezone.now()
            )
    
    def strasse(self, db_bezeichnung):
        qs_fa_strasse = Firma_Strasse.objects.using(db_bezeichnung).filter(firma = self)
        if qs_fa_strasse:
            return qs_fa_strasse.latest('zeitstempel').strasse
        else:
            return None

    # FIRMA HAUSNUMMER
    def hausnummer_ändern(self, db_bezeichnung, neue_hausnummer):
        Firma_Hausnummer.objects.using(db_bezeichnung).create(
            firma = self,
            hausnummer = neue_hausnummer,
            zeitstempel = timezone.now()
            )

    def hausnummer(self, db_bezeichnung):
        qs_fa_hausnummer = Firma_Hausnummer.objects.using(db_bezeichnung).filter(firma = self)
        if qs_fa_hausnummer:
            return qs_fa_hausnummer.latest('zeitstempel').hausnummer
        else:
            return None

    # FIRMA POSTLEITZAHL
    def postleitzahl_ändern(self, db_bezeichnung, neue_postleitzahl):
        Firma_Postleitzahl.objects.using(db_bezeichnung).create(
            firma = self,
            postleitzahl = neue_postleitzahl,
            zeitstempel = timezone.now()
            )

    def postleitzahl(self, db_bezeichnung):
        qs_fa_postleitzahl = Firma_Postleitzahl.objects.using(db_bezeichnung).filter(firma = self)
        if qs_fa_postleitzahl:
            return qs_fa_postleitzahl.latest('zeitstempel').postleitzahl
        else:
            return None

    # FIRMA ORT
    def ort_ändern(self, db_bezeichnung, neuer_ort):
        Firma_Ort.objects.using(db_bezeichnung).create(
            firma = self, 
            ort = neuer_ort,
            zeitstempel = timezone.now()
            )

    def ort(self, db_bezeichnung):
        qs_fa_ort = Firma_Ort.objects.using(db_bezeichnung).filter(firma = self)
        if qs_fa_ort:
            return qs_fa_ort.latest('zeitstempel').ort
        else:
            return None

    # FIRMA EMAIL
    def email_ändern(self, db_bezeichnung, neue_email):
        Firma_Email.objects.using(db_bezeichnung).create(
            firma = self,
            email = neue_email,
            zeitstempel = timezone.now()
            )
    
    def email(self, db_bezeichnung):
        qs_fa_email = Firma_Email.objects.using(db_bezeichnung).filter(firma = self)
        if qs_fa_email:
            return qs_fa_email.latest('zeitstempel')
        else:
            return None

    # FIRMA DICT
    def firma_dict(self, db_bezeichnung):
        fa_dict = self.__dict__
        fa_dict['bezeichnung'] = self.bezeichnung(db_bezeichnung)
        fa_dict['kurzbezeichnung'] = self.kurzbezeichnung(db_bezeichnung)
        fa_dict['strasse'] = self.strasse(db_bezeichnung)
        fa_dict['hausnummer'] = self.hausnummer(db_bezeichnung)
        fa_dict['postleitzahl'] = self.postleitzahl(db_bezeichnung)
        fa_dict['ort'] = self.ort(db_bezeichnung)
        fa_dict['email'] = self.email(db_bezeichnung)
        
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
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable entfernen

class Firma_Gelöscht(models.Model):
    firma = models.ForeignKey(Firma, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Mitarbeiter(AbstractUser):
    firma = models.ForeignKey('Firma', on_delete=models.CASCADE, null = True)
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable löschen

    def __str__(self):
        return self.username

    # MITARBEITER GELÖSCHT
    def löschen(self, db_bezeichnung):
        Mitarbeiter_Gelöscht.objects.using(db_bezeichnung).create(
            mitarbeiter = self,
            gelöscht = True, 
            zeitstempel = timezone.now()
            )

    def entlöschen(self, db_bezeichnung):
        Mitarbeiter_Gelöscht.objects.using(db_bezeichnung).create(
            mitarbeiter = self,
            gelöscht = False, 
            zeitstempel = timezone.now()
            )

    def gelöscht(self, db_bezeichnung):
        return Mitarbeiter_Gelöscht.objects.using(db_bezeichnung).filter(mitarbeiter = self).latest('zeitstempel').gelöscht

    # MITARBEITER FIRMENADMIN
    def firmenadmin_ernennen(self, db_bezeichnung):
        Mitarbeiter_Ist_Firmenadmin.objects.using(db_bezeichnung).create(
            mitarbeiter = self,
            ist_firmenadmin = True,
            zeitstempel = timezone.now()
            )

    def firmenadmin_entheben(self, db_bezeichnung):
        Mitarbeiter_Ist_Firmenadmin.objects.using(db_bezeichnung).create(
            mitarbeiter = self,
            ist_firmenadmin = False,
            zeitstempel = timezone.now()
            )

    def ist_firmenadmin(self, db_bezeichnung):
        return Mitarbeiter_Ist_Firmenadmin.objects.using(db_bezeichnung).filter(mitarbeiter = self).latest('zeitstempel').ist_firmenadmin

    # MITARBEITER SUPERADMIN
    def superadmin_ernennen(self, db_bezeichnung):
        Mitarbeiter_Ist_Superadmin.objects.using(db_bezeichnung).create(
            mitarbeiter = self,
            ist_superadmin = True,
            zeitstempel = timezone.now()
            )
    
    def superadmin_entheben(self, db_bezeichnung):
        Mitarbeiter_Ist_Superadmin.objects.using(db_bezeichnung).create(
            mitarbeiter = self,
            ist_superadmin = False,
            zeitstempel = timezone.now()
            )

    def ist_superadmin(self, db_bezeichnung):
        return Mitarbeiter_Ist_Firmenadmin.objects.using(db_bezeichnung).filter(mitarbeiter = self).latest('zeitstempel').ist_superadmin

    # MITARBEITER PROJEKTADMIN
    def projektadmin_ernennen(self, db_bezeichnung, projekt):
        verbindung_pj_ma = Projekt_Mitarbeiter.objects.using(db_bezeichnung).get(mitarbeiter = self, projekt = projekt)
        if verbindung_pj_ma.aktuell(db_bezeichnung):
            Mitarbeiter_Ist_Projektadmin.objects.using(db_bezeichnung).create(
                projekt_mitarbeiter = verbindung_pj_ma,
                ist_projektadmin = True,
                zeitstempel = timezone.now()
                )

    def projektadmin_entheben(self, db_bezeichnung, projekt):
        verbindung_pj_ma = Projekt_Mitarbeiter.objects.using(db_bezeichnung).get(mitarbeiter = self, projekt = projekt)
        Mitarbeiter_Ist_Projektadmin.objects.using(db_bezeichnung).create(
            projekt_mitarbeiter = verbindung_pj_ma,
            ist_projektadmin = False,
            zeitstempel = timezone.now()
            )

    def ist_projektadmin(self, db_bezeichnung, projekt):
        # Wenn Mitarbeiter nicht mit Projekt verbunden wird False zurückgegeben
        try:
            verbindung_pj_ma = Projekt_Mitarbeiter.objects.using(db_bezeichnung).get(mitarbeiter = self, projekt = projekt)
        except ObjectDoesNotExist:
            return False
        
        return Mitarbeiter_Ist_Projektadmin.objects.using(db_bezeichnung).filter(projekt_mitarbeiter = verbindung_pj_ma).latest('zeitstempel').ist_projektadmin

class Mitarbeiter_Gelöscht(models.Model):
    mitarbeiter = models.ForeignKey(Mitarbeiter, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Mitarbeiter_Ist_Firmenadmin(models.Model):
    mitarbeiter = models.ForeignKey(Mitarbeiter, on_delete = models.CASCADE)
    ist_firmenadmin = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Mitarbeiter_Ist_Superadmin(models.Model):
    mitarbeiter = models.ForeignKey(Mitarbeiter, on_delete = models.CASCADE)
    ist_superadmin = models.BooleanField()
    zeitstempel = models.DateTimeField()

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

class Projekt_Mitarbeiter(models.Model):
    projekt = models.ForeignKey('Projekt', on_delete = models.CASCADE)
    mitarbeiter = models.ForeignKey('Mitarbeiter', on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable entfernen

    def __str__(self):
        return str('%s - %s, %s' % (self.projekt.kurzbezeichnung, self.mitarbeiter.last_name, self.mitarbeiter.first_name,))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ['projekt', 'mitarbeiter'], name = 'verbindung_pj-ma_unique'), # Verbindung Projekt-Mitarbeiter soll unique sein
        ]

class Projekt_Mitarbeiter_Aktuell(models.Model):
    projekt_mitarbeiter = models.ForeignKey(Projekt_Mitarbeiter, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = timezone.now()

class Mitarbeiter_Ist_Projektadmin(models.Model):
    projekt_mitarbeiter = models.ForeignKey(Projekt_Mitarbeiter, on_delete = models.CASCADE)
    ist_projektadmin = models.BooleanField()
    zeitstempel = models.DateTimeField()

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