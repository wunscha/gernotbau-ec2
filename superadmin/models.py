from gernotbau.settings import DB_SUPER
from django import db
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.fields import BooleanField, DateTimeField
from django.db.models.fields.related import ForeignKey
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

###################################################################
# FUNKTIONEN OHNE KLASSE

def liste_alle_firmen():
    li_alle_firmen = []
    for fa in Firma.objects.using(DB_SUPER).all():
        if not fa.gelöscht():
            li_alle_firmen.append(fa)
    return li_alle_firmen

#
###################################################################

class Firma(models.Model):
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable löschen

    # FIRMA GELÖSCHT
    def löschen(self):
        Firma_Gelöscht.objects.using(DB_SUPER).create(
            firma = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def entlöschen(self):
        Firma_Gelöscht.objects.using(DB_SUPER).create(
            firma = self,
            gelöscht = False,
            zeitstempel = timezone.now()
            )

    def gelöscht(self):
        return Firma_Gelöscht.objects.using(DB_SUPER).filter(firma = self).latest('zeitstempel').gelöscht

    # FIRMA BEZEICHNUNG
    def bezeichnung_ändern(self, neue_bezeichnung):
        Firma_Bezeichnung.objects.using(DB_SUPER).create(
            firma = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def _bezeichnung(self):
        return Firma_Bezeichnung.objects.using(DB_SUPER).filter(firma = self).latest('zeitstempel').bezeichnung

    # FIRMA KURZBEZEICHNUNG
    def kurzbezeichnung_ändern(self, neue_kurzbezeichnung):
        Firma_Kurzbezeichnung.objects.using(DB_SUPER).create(
            firma = self,
            kurzbezeichnung = neue_kurzbezeichnung,
            zeitstempel = timezone.now()
            )

    def _kurzbezeichnung(self):
        qs_fa_kurzbezeichnung = Firma_Kurzbezeichnung.objects.using(DB_SUPER).filter(firma = self)
        if qs_fa_kurzbezeichnung:
            return qs_fa_kurzbezeichnung.latest('zeitstempel').kurzbezeichnung
        else:
            return None

    # FIRMA STRASSE
    def strasse_ändern(self, neue_strasse):
        Firma_Strasse.objects.using(DB_SUPER).create(
            firma = self,
            strasse = neue_strasse,
            zeitstempel = timezone.now()
            )
    
    def _strasse(self):
        qs_fa_strasse = Firma_Strasse.objects.using(DB_SUPER).filter(firma = self)
        if qs_fa_strasse:
            return qs_fa_strasse.latest('zeitstempel').strasse
        else:
            return None

    # FIRMA HAUSNUMMER
    def hausnummer_ändern(self, neue_hausnummer):
        Firma_Hausnummer.objects.using(DB_SUPER).create(
            firma = self,
            hausnummer = neue_hausnummer,
            zeitstempel = timezone.now()
            )

    def _hausnummer(self):
        qs_fa_hausnummer = Firma_Hausnummer.objects.using(DB_SUPER).filter(firma = self)
        if qs_fa_hausnummer:
            return qs_fa_hausnummer.latest('zeitstempel').hausnummer
        else:
            return None

    # FIRMA POSTLEITZAHL
    def postleitzahl_ändern(self, neue_postleitzahl):
        Firma_Postleitzahl.objects.using(DB_SUPER).create(
            firma = self,
            postleitzahl = neue_postleitzahl,
            zeitstempel = timezone.now()
            )

    def _postleitzahl(self):
        qs_fa_postleitzahl = Firma_Postleitzahl.objects.using(DB_SUPER).filter(firma = self)
        if qs_fa_postleitzahl:
            return qs_fa_postleitzahl.latest('zeitstempel').postleitzahl
        else:
            return None

    # FIRMA ORT
    def ort_ändern(self, neuer_ort):
        Firma_Ort.objects.using(DB_SUPER).create(
            firma = self, 
            ort = neuer_ort,
            zeitstempel = timezone.now()
            )

    def _ort(self):
        qs_fa_ort = Firma_Ort.objects.using(DB_SUPER).filter(firma = self)
        if qs_fa_ort:
            return qs_fa_ort.latest('zeitstempel').ort
        else:
            return None

    # FIRMA EMAIL
    def email_ändern(self, neue_email):
        Firma_Email.objects.using(DB_SUPER).create(
            firma = self,
            email = neue_email,
            zeitstempel = timezone.now()
            )
    
    def _email(self):
        qs_fa_email = Firma_Email.objects.using(DB_SUPER).filter(firma = self)
        if qs_fa_email:
            return qs_fa_email.latest('zeitstempel').email
        else:
            return None

    # FIRMA PROJEKTADMIN
    def ist_projektadmin_ändern(self, projekt, ist_projektadmin):
        verbindung_pj_fa = Projekt_Firma.objects.using(DB_SUPER).get(firma = self, projekt = projekt)
        Firma_Ist_Projektadmin.objects.using(DB_SUPER).create(
            projekt_firma = verbindung_pj_fa,
            ist_projektadmin = ist_projektadmin,
            zeitstempel = timezone.now( )
            )

    def ist_projektadmin(self, projekt):
        verbindung_pj_fa = Projekt_Firma.objects.using(DB_SUPER).get(firma = self, projekt = projekt)
        return Firma_Ist_Projektadmin.objects.using(DB_SUPER).filter(projekt_firma = verbindung_pj_fa).latest('zeitstempel').ist_projektadmin
    
    # FIRMA MITARBEITER
    def mitarbeiter_anlegen(self, formulardaten, ist_firmenadmin = False):
        User = get_user_model()
        neuer_mitarbeiter = User.objects.using(DB_SUPER).create(
            firma = self,
            zeitstempel = timezone.now(),
            username = formulardaten['email'],
            password = make_password(formulardaten['passwort']),
            first_name = formulardaten['vorname'] if 'vorname' in formulardaten else '',
            last_name  = formulardaten['nachname'] if 'nachname' in formulardaten else ''
            )
        neuer_mitarbeiter.entlöschen()
        ist_firmenadmin = True if ist_firmenadmin in formulardaten else False
        neuer_mitarbeiter.ist_firmenadmin_ändern(ist_firmenadmin = ist_firmenadmin)
        neuer_mitarbeiter.ist_superadmin_ändern(ist_superadmin = False)
        return neuer_mitarbeiter

    def liste_mitarbeiter(self):
        User = get_user_model()
        qs_mitarbeiter = User.objects.using(DB_SUPER).filter(firma = self)
        li_mitarbeiter = []
        for ma in qs_mitarbeiter:
            if not ma.gelöscht():
                li_mitarbeiter.append(ma)
        return li_mitarbeiter

    def liste_mitarbeiter_dict(self):
        li_mitarbeiter_dict = []
        for ma in self.liste_mitarbeiter():
            li_mitarbeiter_dict.append(ma.mitarbeiter_dict())
        return li_mitarbeiter_dict

    '''
    def liste_mitarbeiter_projekt(self, projekt):
        li_ma_pj = []
        for ma in self.liste_mitarbeiter():
            if ma.ist_projektmitarbeiter(projekt):
                li_ma_pj.append(ma)
        return li_ma_pj

    def liste_mitarbeiter_projekt_dict(self, projekt):
        li_ma_pj_dict = []
        for ma in self.liste_mitarbeiter_projekt(projekt):
            dict_ma = ma.mitarbeiter_dict()
            dict_ma['ist_projektadmin'] = ma.ist_projektadmin(projekt)
            li_ma_pj_dict.append(dict_ma)
        return li_ma_pj_dict

    ---> Verbindung Mitarbeiter-Projekt über Rolle ==> Funktionen daher zZt nicht als Model-Funktionen, sondern unter projektadmin/models (ganz unten)
    '''

    # FIRMA LISTE PROJEKTE
    def liste_projekte(self):
        qs_verbindungen_pj_fa = Projekt_Firma.objects.using(DB_SUPER).filter(firma = self)
        li_projekte = []
        for verbindung_pj_fa in qs_verbindungen_pj_fa:
            if verbindung_pj_fa.aktuell() and not verbindung_pj_fa.firma.gelöscht():
                li_projekte.append(verbindung_pj_fa.projekt)
        return li_projekte

    # FIRMA DICT
    def firma_dict(self):
        fa_dict = self.__dict__
        fa_dict['bezeichnung'] = self._bezeichnung()
        fa_dict['kurzbezeichnung'] = self._kurzbezeichnung()
        fa_dict['strasse'] = self._strasse()
        fa_dict['hausnummer'] = self._hausnummer()
        fa_dict['postleitzahl'] = self._postleitzahl()
        fa_dict['ort'] = self._ort()
        fa_dict['email'] = self._email()
        
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
    def löschen(self):
        Mitarbeiter_Gelöscht.objects.using(DB_SUPER).create(
            mitarbeiter = self,
            gelöscht = True, 
            zeitstempel = timezone.now()
            )

    def entlöschen(self):
        Mitarbeiter_Gelöscht.objects.using(DB_SUPER).create(
            mitarbeiter = self,
            gelöscht = False, 
            zeitstempel = timezone.now()
            )

    def gelöscht(self):
        try:
            return Mitarbeiter_Gelöscht.objects.using(DB_SUPER).filter(mitarbeiter = self).latest('zeitstempel').gelöscht
        except ObjectDoesNotExist:
            return False
            
    # MITARBEITER FIRMENADMIN
    def ist_firmenadmin_ändern(self, ist_firmenadmin):
        Mitarbeiter_Ist_Firmenadmin.objects.using(DB_SUPER).create(
            mitarbeiter = self,
            ist_firmenadmin = ist_firmenadmin,
            zeitstempel = timezone.now()
            )

    def ist_firmenadmin(self):
        return Mitarbeiter_Ist_Firmenadmin.objects.using(DB_SUPER).filter(mitarbeiter = self).latest('zeitstempel').ist_firmenadmin

    '''
    ---> Superadmin-Funktionen (Projekt anlegen) noch einrichten
    # MITARBEITER SUPERADMIN
    def ist_superadmin_ändern(self, ist_superadmin):
        Mitarbeiter_Ist_Superadmin.objects.using(DB_SUPER).create(
            mitarbeiter = self,
            ist_superadmin = ist_superadmin,
            zeitstempel = timezone.now()
            )

    def ist_superadmin(self):
        return Mitarbeiter_Ist_Firmenadmin.objects.using(DB_SUPER).filter(mitarbeiter = self).latest('zeitstempel').ist_superadmin
    '''
    # MITARBEITER PROJEKTADMIN
    def projektadmin_ernennen(self, projekt):
        verbindung_pj_fa = Projekt_Firma.objects.using(DB_SUPER).get(projekt = projekt, firma = self.firma)
        firma_ist_projektadmin = Firma_Ist_Projektadmin.objects.using(DB_SUPER).filter(projekt_firma = verbindung_pj_fa).latest('zeitstempel')
        Mitarbeiter_Ist_Projektadmin.objects.using(DB_SUPER).create(
            firma_ist_projektadmin = firma_ist_projektadmin,
            ist_projektadmin = True,
            zeitstempel = timezone.now()
            )

    def projektadmin_entheben(self, projekt):
        verbindung_pj_fa = Projekt_Firma.objects.using(DB_SUPER).get(projekt = projekt, firma = self.firma)
        firma_ist_projektadmin = Firma_Ist_Projektadmin.objects.using(DB_SUPER).filter(projekt_firma = verbindung_pj_fa).latest('zeitstempel')
        Mitarbeiter_Ist_Projektadmin.objects.using(DB_SUPER).create(
            firma_ist_projektadmin = firma_ist_projektadmin,
            ist_projektadmin = False,
            zeitstempel = timezone.now()
            )

    def ist_projektadmin(self, projekt):
        # Wenn Mitarbeiter nicht mit Projekt verbunden wird False zurückgegeben
        try:
            verbindung_pj_fa = Projekt_Firma.objects.using(DB_SUPER).get(projekt = projekt, firma = self.firma)
            firma_ist_projektadmin = Firma_Ist_Projektadmin.objects.using(DB_SUPER).filter(projekt_firma = verbindung_pj_fa).latest('zeitstempel')
            return Mitarbeiter_Ist_Projektadmin.objects.using(DB_SUPER).filter(firma_ist_projektadmin = firma_ist_projektadmin).latest('zeitstempel').ist_projektadmin
        except ObjectDoesNotExist:
            return False

    '''
    # MITARBEITER PROJEKTE
    def liste_projekte(self):
        qs_verbindungen_projekt_mitarbeiter = Projekt_Mitarbeiter.objects.using(DB_SUPER).filter(mitarbeiter = self)
        li_projekte = []
        for verbindung_projekt_mitarbeiter in qs_verbindungen_projekt_mitarbeiter:
            if verbindung_projekt_mitarbeiter.aktuell() and not verbindung_projekt_mitarbeiter.projekt().gelöscht():
                li_projekte.append(verbindung_projekt_mitarbeiter.projekt())
        return li_projekte

    def liste_projekte_dict(self):
        li_projekte_dict = []
        for pj in self.liste_projekte():
            dict_pj = pj.__dict__
            dict_pj['bezeichnung'] = pj.bezeichnung()
            dict_pj['kurzbezeichnung'] = pj.kurzbezeichnung()
            dict_pj['ist_projektadmin'] = self.ist_projektadmin(pj)
            li_projekte_dict.append(dict_pj)
        return li_projekte_dict

    def ist_projektmitarbeiter(self, projekt):
        try:
            verbindung_pj_fa = Projekt_Firma.objects.using(DB_SUPER).get(projekt = projekt, firma = self.firma)
            if verbindung_pj_fa.aktuell():
                verbindung_pj_ma = Projekt_Mitarbeiter.objects.using(DB_SUPER).get(projekt_firma = verbindung_pj_fa, mitarbeiter = self)
                if verbindung_pj_ma.aktuell():
                    return True
                else:
                    return False
        except ObjectDoesNotExist:
            return False
    
    ---> Verbindung Mitarbeiter-Projekt über Rolle ==> Funktionen daher zZt nicht als Model-Funktionen, sondern unter projektadmin/models (ganz unten)
    '''

    # MITARBEITER DICT
    def mitarbeiter_dict(self):
        dict_ma = self.__dict__
        dict_ma['ist_firmenadmin'] = self.ist_firmenadmin()
        
        return dict_ma

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
    def löschen(self):
        Projekt_Gelöscht.objects.using(DB_SUPER).create(
            projekt = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )
        
    def entlöschen(self):
        Projekt_Gelöscht.objects.using(DB_SUPER).create(
            projekt = self,
            gelöscht = False,
            zeitstempel = timezone.now()
            )

    def gelöscht(self):
        Projekt_Gelöscht.objects.using(DB_SUPER).filter(projekt = self).latest('zeitstempel').gelöscht

    # PROJEKT BEZEICHNUNG
    def bezeichnung_ändern(self, neue_bezeichnung):
        Projekt_Bezeichnung.objects.using(DB_SUPER).create(
            projekt = self,
            bezeichnung = neue_bezeichnung, 
            zeitstempel = timezone.now()
            )

    def bezeichnung(self):
        return Projekt_Bezeichnung.objects.using(DB_SUPER).filter(projekt = self).latest('zeitstempel').bezeichnung

    # PROJEKT KURZBEZEICHNUNG
    def kurzbezeichnung_ändern(self, neue_kurzbezeichnung):
        Projekt_Kurzbezeichnung.objects.using(DB_SUPER).create(
            projekt = self,
            kurzbezeichnung = neue_kurzbezeichnung,
            zeitstempel = timezone.now()
            )

    def kurzbezeichnung(self):
        try:
            return Projekt_Kurzbezeichnung.objects.using(DB_SUPER).filter(projekt = self).latest('zeitstempel').kurzbezeichnung
        except ObjectDoesNotExist:
            return None

    # PROJEKT DB_BEZEICHNUNG
    def db_bezeichnung_ändern(self, neue_db_bezeichnung):
        Projekt_DB.objects.using(DB_SUPER).create(
            projekt = self,
            db_bezeichnung = neue_db_bezeichnung,
            zeitstempel = timezone.now()
            )
    
    def db_bezeichnung(self):
        return Projekt_DB.objects.using(DB_SUPER).filter(projekt = self).latest('zeitstempel').db_bezeichnung

    # PROJEKT FIRMEN
    def liste_projektfirmen(self):
        li_firmen = []
        for verbindung_pj_fa in Projekt_Firma.objects.using(DB_SUPER).filter(projekt = self):
            if verbindung_pj_fa.aktuell() and not verbindung_pj_fa.firma.gelöscht():
                li_firmen.append(verbindung_pj_fa.firma)
        return li_firmen

    def liste_projektfirmen_dicts(self):
        li_firmen_dicts = []
        for fa in self.liste_projektfirmen():
            fa_dict = fa.firma_dict()
            fa_dict['ist_projektadmin'] = self.firma_ist_projektadmin(fa)
            li_firmen_dicts.append(fa_dict)
        return li_firmen_dicts

    def liste_nicht_projektfirmen(self):
        li_nicht_projektfirmen = []
        for fa in liste_alle_firmen():
            if not fa in self.liste_projektfirmen():
                li_nicht_projektfirmen.append(fa)
        return li_nicht_projektfirmen
    
    def liste_nicht_projektfirmen_dicts(self):
        li_nicht_projektfirmen_dicts = []
        for fa in self.liste_nicht_projektfirmen():
            li_nicht_projektfirmen_dicts.append(fa.firma_dict())
        return li_nicht_projektfirmen_dicts

    def firma_anlegen(self, formulardaten, ist_projektadmin = False):
        # Firma anlegen
        neue_firma = Firma.objects.using(DB_SUPER).create(
            zeitstempel = timezone.now()
            )
        neue_firma.bezeichnung_ändern(formulardaten['bezeichnung'])
        neue_firma.kurzbezeichnung_ändern(formulardaten['kurzbezeichnung'])
        neue_firma.strasse_ändern(formulardaten['strasse'])
        neue_firma.hausnummer_ändern(formulardaten['hausnummer'])
        neue_firma.postleitzahl_ändern(formulardaten['postleitzahl'])
        neue_firma.ort_ändern(formulardaten['ort'])
        neue_firma.email_ändern(formulardaten['email'])
        neue_firma.entlöschen()
        self.firma_verbinden(neue_firma)
        self.firma_ist_projektadmin_ändern(firma = neue_firma, ist_projektadmin = ist_projektadmin)
        
        # Firmenadmin anlegen
        neue_firma.mitarbeiter_anlegen(formulardaten, ist_firmenadmin = True)

        return neue_firma

    def firma_verbinden(self, firma, ist_projektadmin = False):
        verbindung_pj_fa = Projekt_Firma.objects.using(DB_SUPER).get_or_create(
            projekt = self,
            firma = firma,
            defaults = {'zeitstempel': timezone.now()}
            )[0]
        verbindung_pj_fa.aktualisieren()
        self.firma_ist_projektadmin_ändern(firma = firma, ist_projektadmin = ist_projektadmin)

    def firma_lösen(self, firma):
        verbindung_pj_fa = Projekt_Firma.objects.using(DB_SUPER).get(projekt = self, firma = firma)
        verbindung_pj_fa.entaktualisieren()

    # PROJEKT MITARBEITER
    '''
    def mitarbeiter_verbinden(self, mitarbeiter):
        verbindung_pj_fa = Projekt_Firma.objects.using(DB_SUPER).get(
            projekt = self,
            firma = mitarbeiter.firma
            )
        verbindung_pj_ma = Projekt_Mitarbeiter.objects(DB_SUPER).get_or_create(
            projekt_firma = verbindung_pj_fa,
            mitarbeiter = mitarbeiter,
            defaults = {'zeitstempel': timezone.now()},
            )
        verbindung_pj_ma.aktualisieren()

    def mitarbeiter_lösen(self):
        pass

    def liste_projektmitarbeiter(self):
        pass

    def liste_projektmitarbeiter_dict(self):
        pass
    
    def liste_projektmitarbeiter_firma(self, firma):
        pass

    def liste_projektmitarbeiter_firma_dict(self, firma):
        pass
    
    ---> Verbindung Projekt-Mitarbeiter über Rolle. Funktionen dzt nicht als Model-Funktionen wegen zirkulärem Import. Funktionen siehe Projektadmin-Models ganz unten
    '''

    # PROJEKT FIRMA IST PROJEKTADMIN
    def firma_ist_projektadmin_ändern(self, firma, ist_projektadmin):
        verbindung_pj_fa = Projekt_Firma.objects.using(DB_SUPER).get(projekt = self, firma = firma)
        Firma_Ist_Projektadmin.objects.using(DB_SUPER).create(
            projekt_firma = verbindung_pj_fa,
            ist_projektadmin = ist_projektadmin,
            zeitstempel = timezone.now()
            )

    def firma_ist_projektadmin(self, firma):
        verbindung_pj_fa = Projekt_Firma.objects.using(DB_SUPER).get(projekt = self, firma = firma)
        return Firma_Ist_Projektadmin.objects.using(DB_SUPER).filter(projekt_firma = verbindung_pj_fa).latest('zeitstempel').ist_projektadmin

    # PROJEKT DICT
    def projekt_dict(self):
        dict_pj = self.__dict__
        dict_pj['bezeichnung'] = self.bezeichnung()
        dict_pj['kurzbezeichnung'] = self.kurzbezeichnung()

        return dict_pj

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

class Projekt_Firma(models.Model):
    projekt = models.ForeignKey('Projekt', on_delete = models.CASCADE)
    firma = models.ForeignKey('Firma', on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField(null = True) # Nullable entfernen

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ['projekt', 'firma'], name = 'verbindung_pj-fa_unique') # Verbindung Projekt-Firma soll unique sein
        ]

    # PROJEKT_FIRMA AKTUELL
    def aktualisieren(self):
        Projekt_Firma_Aktuell.objects.using(DB_SUPER).create(
            projekt_firma = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self):
        Projekt_Firma_Aktuell.objects.using(DB_SUPER).create(
            projekt_firma = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )

    def aktuell(self):
        return Projekt_Firma_Aktuell.objects.using(DB_SUPER).filter(projekt_firma = self).latest('zeitstempel').aktuell

class Projekt_Firma_Aktuell(models.Model):
    projekt_firma = models.ForeignKey(Projekt_Firma, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Firma_Ist_Projektadmin(models.Model):
    projekt_firma = models.ForeignKey(Projekt_Firma, on_delete = models.CASCADE)
    ist_projektadmin = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Mitarbeiter_Ist_Projektadmin(models.Model):
    # Zeigt auf 'Firma ist Projektadmin' --> dadurch kann MA nur Projektadmin sein wenn auch FA Projektadmin ist    
    firma_ist_projektadmin = models.ForeignKey(Firma_Ist_Projektadmin, on_delete = models.CASCADE, null = True) # TODO: Nullable entfernen
    ist_projektadmin = models.BooleanField()
    zeitstempel = models.DateTimeField()

'''
class Projekt_Mitarbeiter(models.Model):
    projekt_firma = models.ForeignKey(Projekt_Firma, on_delete = models.CASCADE, null = True) # TODO: Nullable entfernen
    mitarbeiter = models.ForeignKey(Mitarbeiter, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField(null = True) # TODO: Nullable entfernen

    # PROJEK_MITARBEITER PROJEKT
    def projekt(self):
        return self.projekt_firma.projekt

    # PROJEKT_MITARBEITER AKTUELL
    def aktualisieren(self):
        Projekt_Mitarbeiter_Aktuell.objects.using(DB_SUPER).create(
            projekt_mitarbeiter = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )

    def entaktualisieren(self):
        Projekt_Mitarbeiter_Aktuell.objects.using(DB_SUPER).create(
            projekt_mitarbeiter = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )
    
    def aktuell(self):
        try:
            return Projekt_Mitarbeiter_Aktuell.objects.using(DB_SUPER).filter(projekt_mitarbeiter = self).latest('zeitstempel').aktuell
        except ObjectDoesNotExist:
            return False

    def __str__(self):
        return str('%s - %s, %s' % (self.projekt.kurzbezeichnung, self.mitarbeiter.last_name, self.mitarbeiter.first_name,))

    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ['projekt', 'mitarbeiter'], name = 'verbindung_pj-ma_unique'), # Verbindung Projekt-Mitarbeiter soll unique sein
        ]
---> Model in Projektadmin Models verschoben (MA ist über Rolle mit PJ verbunden)

class Projekt_Mitarbeiter_Aktuell(models.Model):
    projekt_mitarbeiter = models.ForeignKey(Projekt_Mitarbeiter, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = timezone.now()
---> Model in Projektadmin Models verschoben (MA ist über Rolle mit PJ verbunden)
'''