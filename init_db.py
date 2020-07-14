# -*- coding: utf-8 -*-
"""
Fill tables with secondary information
Created on Sun Apr 12 07:41:31 2020

@author: Alex
"""

from app import db
from app.models import Chemical, Medium, Person, Cell_line, Endpoint, Solvent, \
    Person_Institution, Institution
import  os
import pandas as pd

db.create_all()
session = db.session


#add media
with open(os.path.join(".", "data", "media.csv"), 'r') as f:
    media_info = pd.read_csv(f)
session.bulk_insert_mappings(Medium, media_info.to_dict(orient='rows'))

#add endpoints
with open(os.path.join(".", "data", "endpoints.csv"), 'r') as f:
    endpoint_info = pd.read_csv(f)
session.bulk_insert_mappings(Endpoint, endpoint_info.to_dict(orient='rows'))

#add solvents
with open(os.path.join(".", "data", "solvents.csv"), 'r') as f:
    solvent_info = pd.read_csv(f, sep=';')
session.bulk_insert_mappings(Solvent, solvent_info.to_dict(orient='rows'))

#add chemicals
chu = pd.read_excel(os.path.join(".","data","chemicals_unique.xlsx"))
session.bulk_insert_mappings(Chemical,chu.to_dict(orient="rows"))
session.commit()


#add Persons and institutions Institutions
perXls = pd.ExcelFile(os.path.join(".", "data", "experimenters_filled.xlsx"))

perSheet = pd.read_excel(perXls, "Person")
instSheet = pd.read_excel(perXls, "Institution")
perInstSheet = pd.read_excel(perXls, "Person_Institution")

perInstSheet['end_year'] = perInstSheet['end_year'].replace("present",
                                                            10000).astype(int)

perSheet.to_sql("person",
                db.engine,
                if_exists='append',
                schema='public',
                index=False,
                chunksize=500)

instSheet.to_sql("institution",
                 db.engine,
                 if_exists='append',
                 schema='public',
                 index=False,
                 chunksize=500)

piDicts = []

for rec in perInstSheet.to_dict(orient="records"):
    person_id = session.query(
        Person.id).filter_by(short_name=rec['person']).one()[0]
    institution_id = session.query(
        Institution.id).filter_by(short_name=rec['institution']).one()[0]
    piDicts.append({
        "person_id": person_id,
        "institution_id": institution_id,
        "start_year": rec["start_year"],
        "end_year": rec["end_year"]
    })
session.bulk_insert_mappings(Person_Institution, piDicts)
session.commit()

with open(os.path.join(".", "data", "cell_lines.csv"), 'r') as f:
    cell_line = pd.read_csv(f, sep=",")

session.bulk_insert_mappings(Cell_line, cell_line.to_dict(orient='rows'))

session.commit()
session.close()
