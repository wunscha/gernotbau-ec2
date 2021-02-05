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
        '10': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': '10',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': 'db',
            'PORT': 5432
            },
        'furz': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'furz',
            'USER': 'postgres',
            'PASSWORD': 'postgres',
            'HOST': 'db',
            'PORT': 5432
            },
        }