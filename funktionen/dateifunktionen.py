def speichere_datei_chunks(datei, zielpfad):
    with open(zielpfad + datei.name, 'wb+') as ziel:
        for chunk in datei.chunks():
            ziel.write(chunk)