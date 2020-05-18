# -*- coding: utf-8 -*-
"""
Created on Sun Apr 12 07:41:31 2020

@author: Alex
"""
#from sqlalchemy.orm import sessionmaker
#from sqlalchemy import create_engine
from app import db
from app.models import Chemical, Medium, Experimenter, Cell_line, Endpoint, Solvent
import json, os,csv
import pandas as pd

#engine = create_engine("postgresql+psycopg2://utox_admin:iLoveCellLines@/cell_tox_db")




#DBSession = sessionmaker(bind=engine)
#session = DBSession()


db.create_all()
session = db.session

with open(os.path.join(".","data","media.csv"),'r') as f:
    media_info = pd.read_csv(f)
session.bulk_insert_mappings(Medium,
                             media_info.to_dict(orient='rows'))

with open(os.path.join(".","data","endpoints.csv"),'r') as f:
    endpoint_info = pd.read_csv(f)
session.bulk_insert_mappings(Endpoint,
                             endpoint_info.to_dict(orient='rows'))

with open(os.path.join(".","data","solvents.csv"),'r') as f:
    solvent_info = pd.read_csv(f,sep=';'  )
session.bulk_insert_mappings(Solvent,
                             solvent_info.to_dict(orient='rows'))


with open(os.path.join(".","data","chemicals_info.json"),'r') as f:
    ch_info = json.load(f)
    

session.bulk_insert_mappings(Chemical,ch_info)

session.commit()


session.add(Experimenter(short_name ="jen",full_name = "Jenny Maner"))
session.add(Experimenter(short_name ="fab",full_name = "Fabian Balk"))
session.add(Experimenter(short_name ="gay",full_name = "Gayathri Jaikumar"))
session.add(Experimenter(short_name ="hél",full_name = "Helen Mottaz"))
session.add(Experimenter(short_name ="mar",full_name = "Maren"))
session.add(Experimenter(short_name ="han",full_name = "Hannah Schug"))
session.add(Experimenter(short_name ="mir",full_name = "Miriam"))
session.add(Experimenter(short_name ="kat",full_name = "Katrin"))
session.add(Experimenter(short_name ="jul",full_name = "Julita"))
session.add(Experimenter(short_name ="nev",full_name = "Nev"))

session.add(Cell_line(short_name ="GIL",full_name = "RTgill-W1",organism = "O. mykiss", tissue = "gill"))
session.add(Cell_line(short_name ="GUT",full_name = "RTgutGC",organism = "O. mykiss", tissue = "gut"))


session.commit()
session.close()





