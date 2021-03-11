from datetime import time
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.fields import CharField, DateTimeField
from django.utils import timezone

from os import path

from projektadmin.models import Pfad_Anhaenge, Pfad_Fotos, Pfad_Projekt, Status, Datei
from superadmin.models import Firma, Mitarbeiter
from gernotbau.settings import DB_SUPER

class Ticket(models.Model):
    aussteller_id = CharField(max_length = 20)
    zeitstempel = DateTimeField()

    # TICKET GELÖSCHT
    def _löschen(self, pj):
        Ticket_Gelöscht.objects.using(pj.db_bezeichnung()).create(
            ticket = self, 
            gelöscht = True,
            zeitstempel = timezone.now()
            )

    def _entlöschen(self, pj):
        Ticket_Gelöscht.objects.using(pj.db_bezeichnung()).create(
            ticket = self, 
            gelöscht = False,
            zeitstempel = timezone.now()
            )

    def _gelöscht(self, pj):
        try:
            return Ticket_Gelöscht.objects.using(pj.db_bezeichnung()).filter(ticket = self).latest('zeitstempel').gelöscht
        except ObjectDoesNotExist:
            return False

    # TICKET BEZEICHNUNG
    def _bezeichnung_ändern(self, pj, bezeichnung_neu):
        Ticket_Bezeichnung.objects.using(pj.db_bezeichnung()).create(
            ticket = self,
            bezeichnung = bezeichnung_neu,
            zeitstempel = timezone.now(),
            )
    
    def _bezeichnung(self, pj):
        return Ticket_Bezeichnung.objects.using(pj.db_bezeichnung()).filter(ticket = self).latest('zeitstempel').bezeichnung

    # TICKET STATUS AUSSTELLER
    def _ausstellerstatus(self, pj):
        ticket_ausstellerstatus = Ticket_Ausstellerstatus.objects.using(pj.db_bezeichnung()).filter(ticket = self).latest('zeitstempel')
        return ticket_ausstellerstatus.status

    # TICKET X-KOORDINATE
    def _x_koordinate_ändern(self, pj, plan, x_koordinate_neu):
        ti_pl = Ticket_Plan.objects.using(pj.db_bezeichnung()).get(ticket = self, plan = plan)
        Ticket_Plan_X.objects.using(pj.db_bezeichnung()).create(
            ticket_plan = ti_pl,
            x_koordinate = x_koordinate_neu,
            zeitstempel = timezone.now()
            )
    
    def _x_koordinate(self, pj, plan):
        ti_pl = Ticket_Plan.objects.using(pj.db_bezeichnung()).get(ticket = self, plan = plan)
        return Ticket_Plan_X.objects.using(pj.db_bezeichnung()).filter(ticket_plan = ti_pl).latest('zeitstempel').x_koordinate

    # TICKET Y-KOORDINATE
    def _y_koordinate_ändern(self, pj, plan, y_koordinate_neu):
        ti_pl = Ticket_Plan.objects.using(pj.db_bezeichnung()).get(ticket = self, plan = plan)
        Ticket_Plan_Y.objects.using(pj.db_bezeichnung()).create(
            ticket_plan = ti_pl,
            y_koordinate = y_koordinate_neu,
            zeitstempel = timezone.now()
            )
    
    def _y_koordinate(self, pj, plan):
        ti_pl = Ticket_Plan.objects.using(pj.db_bezeichnung()).get(ticket = self, plan = plan)
        return Ticket_Plan_Y.objects.using(pj.db_bezeichnung()).filter(ticket_plan = ti_pl).latest('zeitstempel').y_koordinate

    # TICKET EMPFÄNGERGIRMA
    def _empfängerfirma_ändern(self, pj, empfängerfirma_neu_id):
        ti_empf = Ticket_Empfängerfirma.objects.using(pj.db_bezeichnung()).create(
            ticket = self,
            firma_id = empfängerfirma_neu_id,
            zeitstempel = timezone.now()
            )
        return ti_empf

    def _empfängerfirma(self, pj):
        ti_empf_id = Ticket_Empfängerfirma.objects.using(pj.db_bezeichnung()).filter(ticket = self).latest('zeitstempel').firma_id
        return Firma.objects.using(DB_SUPER).get(pk = ti_empf_id)

    def _empfängerfirma_gelesen_markieren(self, pj):
        ti_empf = Ticket_Empfängerfirma.objects.using(pj.db_bezeichnung()).filter(ticket = self).latest('zeitstempel')
        Ticket_Empfängerfirma_Gelesen.objects.using(pj.db_bezeichnung()).create(
            ticket_empfängerfirma = ti_empf,
            zeitstempel = timezone.now()
            )

    def _empfängerfirma_gelesen(self, pj):
        ticket_empfängerfirma = Ticket_Empfängerfirma.objects.using(pj.db_bezeichnung()).filter(ticket = self).latest('zeitstempel')
        return ticket_empfängerfirma._gelesen(pj)
        
    def _empfängerstatus(self, pj):
        ticket_empfängerfirma = Ticket_Empfängerfirma.objects.using(pj.db_bezeichnung()).filter(ticket = self).latest('zeitstempel')
        return ticket_empfängerfirma._status(pj)

    # TICKET FÄLLIGKEITSDATUM
    def _fälligkeitsdatum_ändern(self, pj, fälligkeitsdatum_neu):
        Ticket_Fälligkeitsdatum.objects.using(pj.db_bezeichnung()).create(
            ticket = self,
            zeitstempel = timezone.now(),
            fälligkeitsdatum = fälligkeitsdatum_neu
            )

    def _fälligkeitsdatum(self, pj):
        qs_ticket_fälligkeitsdatum = Ticket_Fälligkeitsdatum.objects.using(pj.db_bezeichnung()).filter(ticket = self)
        return qs_ticket_fälligkeitsdatum.latest('zeitstempel').fälligkeitsdatum

    # TICKET PLAN
    def _plan(self, pj):
        qs_ti_pl = Ticket_Plan.objects.using(pj.db_bezeichnung()).filter(ticket = self)
        return qs_ti_pl.latest('zeitstempel').plan

    # TICKET HISTORIE
    def _historie(self, pj):
        
        User = get_user_model()
        li_historie = []
        
        # Erstellt
        dict_eintrag_erstellt = {}
        dict_eintrag_erstellt['ereignis'] = 'Ticket erstellt'
        ma = User.objects.using(DB_SUPER).get(pk = self.aussteller_id)
        dict_eintrag_erstellt['mitarbeiter_firma'] = f'{ma.first_name} {ma.last_name}'
        dict_eintrag_erstellt['zeitstempel'] = self.zeitstempel
        dict_eintrag_erstellt['text'] = 'Ticket erstellt'

        li_historie.append(dict_eintrag_erstellt)

        # Kommentare
        for k in Ticket_Kommentar.objects.using(pj.db_bezeichnung()).filter(ticket = self):
            dict_eintrag_kommentar = {}
            dict_eintrag_kommentar['ereignis'] = 'Kommentar'
            ma = User.objects.using(DB_SUPER).get(pk = k.mitarbeiter_id)
            dict_eintrag_kommentar['mitarbeiter_firma'] = f'{ma.first_name} {ma.last_name}'
            dict_eintrag_kommentar['zeitstempel'] = k.zeitstempel
            dict_eintrag_kommentar['text'] = k.text

            # Kommentar-Anhänge
            pfad_projekt = Pfad_Projekt.objects.using(pj.db_bezeichnung()).latest('zeitstempel').pfad
            pfad_anhänge = Pfad_Anhaenge.objects.using(pj.db_bezeichnung()).latest('zeitstempel').pfad
            li_anhänge = []
            for a in Ticket_Kommentar_Anhang.objects.using(pj.db_bezeichnung()).filter(ticket_kommentar = k):
                dict_a = a.__dict__
                dict_a['dateiname'] = a.datei.dateiname
                dict_a['dateipfad'] = path.join(pfad_projekt, pfad_anhänge, f'{a.datei.id}_{a.datei.dateiname}')
                li_anhänge.append(dict_a)
            dict_eintrag_kommentar['liste_anhänge'] = li_anhänge

            # Kommentar-Fotos
            pfad_fotos = Pfad_Fotos.objects.using(pj.db_bezeichnung()).latest('zeitstempel').pfad
            li_fotos = []
            for fo in Ticket_Kommentar_Foto.objects.using(pj.db_bezeichnung()).filter(ticket_kommentar = k):
                dict_fo = fo.__dict__
                dict_fo['dateiname'] = fo.foto.dateiname
                dict_fo['dateipfad'] = path.join(pfad_projekt, pfad_fotos, f'{fo.foto.id}_{fo.foto.dateiname}')
                li_fotos.append(dict_fo)
            dict_eintrag_kommentar['liste_fotos'] = li_fotos

            li_historie.append(dict_eintrag_kommentar)

        # Ausstellerstati
        for ast in Ticket_Ausstellerstatus.objects.using(pj.db_bezeichnung()).filter(ticket = self):
            dict_eintrag_ausstellerstatus = {}
            dict_eintrag_ausstellerstatus['ereignis'] = 'Status Aussteller'
            ma = User.objects.using(DB_SUPER).get(pk = self.aussteller_id)
            dict_eintrag_ausstellerstatus['mitarbeiter_firma'] = f'{ma.first_name} {ma.last_name}'
            dict_eintrag_ausstellerstatus['zeitstempel'] = ast.zeitstempel
            dict_eintrag_ausstellerstatus['text'] = f'Ausstellerstatus geändert auf: {ast.status.bezeichnung}'

            li_historie.append(dict_eintrag_ausstellerstatus)

        # Empfängerstatus
        ti_empf = Ticket_Empfängerfirma.objects.using(pj.db_bezeichnung()).filter(ticket = self).latest('zeitstempel')
        for es in Ticket_Empfängerfirma_Status.objects.using(pj.db_bezeichnung()).filter(ticket_empfängerfirma = ti_empf):
            dict_eintrag_empfängerstatus = {}
            dict_eintrag_empfängerstatus['ereignis'] = 'Status Empfängerfirma'
            fa = Firma.objects.using(DB_SUPER).get(pk = ti_empf.firma_id)
            dict_eintrag_empfängerstatus['mitarbeiter_firma'] = fa._bezeichnung()
            dict_eintrag_empfängerstatus['zeitstempel'] = es.zeitstempel
            dict_eintrag_empfängerstatus['text'] = f'Empfängerstatus geändert auf: {es.status.bezeichnung}'

            li_historie.append(dict_eintrag_empfängerstatus)

        return sorted(li_historie, key = lambda i: i['zeitstempel'])

    # TICKET DICT
    def _dict_für_übersicht(self, pj):
        dict_ticket = self.__dict__
        dict_ticket['bezeichnung'] = self._bezeichnung(pj)
        User = get_user_model()
        ma = User.objects.using(DB_SUPER).get(pk = self.aussteller_id)
        dict_ticket['aussteller'] = ma.first_name + ' ' + ma.last_name
        dict_ticket['ausstellerstatus'] = self._ausstellerstatus(pj).bezeichnung
        # Empfängerfirma
        dict_empfängerfirma = self._empfängerfirma(pj).__dict__
        dict_empfängerfirma['bezeichnung'] = self._empfängerfirma(pj)._bezeichnung()
        dict_ticket['empfängerfirma'] = dict_empfängerfirma
        dict_ticket['empfängerstatus'] = self._empfängerstatus(pj).bezeichnung
        dict_ticket['gelesen'] = self._empfängerfirma_gelesen(pj)
        dict_ticket['fälligkeitsdatum'] = self._fälligkeitsdatum(pj)
        dict_ticket['plan'] = self._plan(pj)._bezeichnung(pj)

        return dict_ticket

class Ticket_Gelöscht(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Ticket_Bezeichnung(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 25)
    zeitstempel = models.DateTimeField()

class Ticket_Fälligkeitsdatum(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete = models.CASCADE)
    zeitstempel = DateTimeField()
    fälligkeitsdatum = DateTimeField()

class Ticket_Ausstellerstatus(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete = models.CASCADE)
    status = models.ForeignKey(Status, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

class Ticket_Empfängerfirma(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete = models.CASCADE)
    firma_id = models.CharField(max_length = 20)
    zeitstempel = models.DateTimeField()

    # TICKET_EMPFÄNGERFIRMA AKTUELL
    def _aktualisieren(self, pj):
        Ticket_Empfängerfirma_Aktuell.objects.using(pj.db_bezeichnung()).create(
            ticket_empfängerfirma = self,
            aktuell = True,
            zeitstempel = timezone.now()
            )
    
    def _entaktualisieren(self, pj):
        Ticket_Empfängerfirma_Aktuell.objects.using(pj.db_bezeichnung()).create(
            ticket_empfängerfirma = self,
            aktuell = False,
            zeitstempel = timezone.now()
            )
    
    def _aktuell(self, pj):
        try:
            return Ticket_Empfängerfirma_Aktuell.objects.using(pj.db_bezeichnung()).filter(ticket_empfängerfirma = self).latest('zeitstempel').aktuell
        except ObjectDoesNotExist:
            return None

    # TICKET_EMPFÄNGERFIRMA GELESEN
    def _gelesen(self, pj):
        qs_gel = Ticket_Empfängerfirma_Gelesen.objects.using(pj.db_bezeichnung()).filter(ticket_empfängerfirma = self)
        if qs_gel:
            return True
        else:
            return False

    # TICKET_EMPFÄNGERFIRMA STATUS
    def _status(self, pj):
        ti_empf = Ticket_Empfängerfirma_Status.objects.using(pj.db_bezeichnung()).filter(ticket_empfängerfirma = self).latest('zeitstempel')
        return ti_empf.status

class Ticket_Empfängerfirma_Aktuell(models.Model):
    ticket_empfängerfirma = models.ForeignKey(Ticket_Empfängerfirma, on_delete = models.CASCADE)
    aktuell = models.BooleanField()
    zeitstempel = timezone.now()

class Ticket_Empfängerfirma_Gelesen(models.Model):
    ticket_empfängerfirma = models.ForeignKey(Ticket_Empfängerfirma, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

class Ticket_Empfängerfirma_Status(models.Model):
    ticket_empfängerfirma = models.ForeignKey(Ticket_Empfängerfirma, on_delete = models.CASCADE)
    status = models.ForeignKey(Status, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

class Ticket_Kommentar(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete = models.CASCADE)
    mitarbeiter_id = models.CharField(max_length = 20)
    text = models.CharField(max_length = 250)
    zeitstempel = models.DateTimeField()

class Ticket_Kommentar_Anhang(models.Model):
    ticket_kommentar = models.ForeignKey(Ticket_Kommentar, on_delete = models.CASCADE)
    datei = models.ForeignKey(Datei, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

class Ticket_Kommentar_Foto(models.Model):
    ticket_kommentar = models.ForeignKey(Ticket_Kommentar, on_delete = models.CASCADE)
    foto = models.ForeignKey(Datei, on_delete = models.CASCADE)
    breite_px = models.IntegerField(null = True) # TODO: Nullable entfernen
    hoehe_px = models.IntegerField(null = True) # TODO: Nullable entfernen
    zeitstempel = models.DateTimeField()

class Plan(models.Model):
    breite = models.FloatField()
    hoehe = models.FloatField()
    datei = models.ForeignKey(Datei, on_delete = models.CASCADE)

    # PLAN BEZEICHNUNG
    def _bezeichnung_ändern(self, pj, neue_bezeichnung):
        Plan_Bezeichnung.objects.using(pj.db_bezeichnung()).create(
            plan = self,
            bezeichnung = neue_bezeichnung,
            zeitstempel = timezone.now()
            )

    def _bezeichnung(self, pj):
        qs_plan_bez = Plan_Bezeichnung.objects.using(pj.db_bezeichnung()).filter(plan = self)
        return qs_plan_bez.latest('zeitstempel').bezeichnung

    # PLAN GELÖSCHT
    def _löschen(self, pj):
        Plan_Gelöscht.objects.using(pj.db_bezeichnung()).create(
            plan = self,
            gelöscht = True,
            zeitstempel = timezone.now()
            )
    
    def _entlöschen(self, pj):
        Plan_Gelöscht.objects.using(pj.db_bezeichnung()).create(
            plan = self,
            gelöscht = False,
            zeitstempel = timezone.now()
            )

    def _gelöscht(self, pj):
        try:
            qs_plan_gelöscht = Plan_Gelöscht.objects.using(pj.db_bezeichnung()).filter(plan = self)
            return qs_plan_gelöscht.latest('zeitstempel').gelöscht
        except ObjectDoesNotExist:
            return False

class Plan_Bezeichnung(models.Model):
    plan = models.ForeignKey(Plan, on_delete = models.CASCADE)
    bezeichnung = models.CharField(max_length = 25)
    zeitstempel = models.DateTimeField()

class Plan_Gelöscht(models.Model):
    plan = models.ForeignKey(Plan, on_delete = models.CASCADE)
    gelöscht = models.BooleanField()
    zeitstempel = models.DateTimeField()

class Ticket_Plan(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete = models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete = models.CASCADE)
    zeitstempel = models.DateTimeField()

class Ticket_Plan_X(models.Model):
    ticket_plan = models.ForeignKey(Ticket_Plan, on_delete = models.CASCADE)
    x_koordinate = models.FloatField()
    zeitstempel = models.DateTimeField()

class Ticket_Plan_Y(models.Model):
    ticket_plan = models.ForeignKey(Ticket_Plan, on_delete = models.CASCADE)
    y_koordinate = models.FloatField()
    zeitstempel = models.DateTimeField()

class Pfad_Plaene(models.Model):
    pfad = models.CharField(max_length = 100)
    zeitstempel = models.DateTimeField()
