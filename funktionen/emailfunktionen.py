from superadmin.models import Mitarbeiter, Firma

def generiere_email_adresse_ma(*, firma, nachname):
# Generiert Email Adresse für Mitarbeiter (prüft ob Adresse schon vorhanden)

    email_doppelt = False
    emailzähler = ''
    
    # Schleife solange durchlaufen, bis keim MA mit E-Mailadresse mehr vorhanden
    while True:
        email_doppelt = False
        email = nachname.lower() + str(emailzähler) + '.' + firma.email
        if Mitarbeiter.objects.using('default').filter(email = email):
            email_doppelt = True
            emailzähler = 1 if emailzähler == '' else emailzähler + 1
        if not email_doppelt:
            break
    
    return email

def generiere_email_adresse_fa(*, kurzbezeichnung):
# Generiert Email Adresse für Firma (prüft ob Adresse schon vorhanden)

    email_doppelt = False
    emailzähler = ''
    
    # Schleife solange durchlaufen, bis keine Firma mit E-Mailadresse mehr vorhanden
    while True:
        email_doppelt = False
        email = kurzbezeichnung.lower() + str(emailzähler) + '@gernotbau.at'
        if Firma.objects.using('default').filter(email = email):
            email_doppelt = True
            emailzähler = 1 if emailzähler == '' else emailzähler + 1
        if not email_doppelt:
            break
    
    return email