from psycopg2 import connect
import sys
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def lege_datenbank_an(db_bezeichnung, user = 'postgres', password = 'postgres', host = 'db'):
    #
    con = None
    con = connect(user = user, password = password, host = host)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    cur.execute(f'CREATE DATABASE f{db_bezeichnung};')
    cur.close()
    con.close()

def dict_databases():
    return {
        'default':{
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'postgres',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': 'db',
            'PORT': 5432
            },
        'pj_18': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'furz2',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': 'db',
            'PORT': 5432
            },
        'pj_19': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'projekt_19',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': 'db',
            'PORT': 5432
            },
        }