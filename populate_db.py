# -*- coding: utf-8 -*-
"""
Populate the database with exposure entries.

Created on Wed Apr 22 18:40:12 2020

@author: Alex
"""
import app
from insert_db import add_record
from fileIO import read_dr

import os

db = app.db
Chemical = app.db.models.Chemical
Nanomaterial = app.db.models.Nanomaterial
Exposure = app.db.models.Exposure

#get list of rawdata file names
files = list(
    filter(
        lambda x: (x.endswith("xls") or x.endswith("xlsx") or x.endswith("csv")
                   ) and not x.startswith('.') and not x.startswith('~'),
        os.listdir('../rawdata/newnames')))

#read raw files
data = [
    read_dr(os.path.join("..", "rawdata", "newnames", fname), verbose=True)
    for fname in files
]


#add_record(data[0], db.session, db.engine)

#add exposures to database
failed = []
failed_files = []
for i, d in enumerate(data):
    try:
        add_record(d, db.session, db.engine)
    except:
        failed.append(d["id_string"])
        failed_files.append(files[i])
        

#assign dabase models from app to prevent double import
Person = app.models.Person
Institution = app.models.Institution
Person_Institution = app.models.Person_Institution

#add institution to exposure according to the affiliation of the experimenter
seq = app.db.session.query
q = seq(Person).join(Person_Institution)
qwe = q.with_entities(Person.id, Person_Institution.institution_id).all()
updict = [{"experimenter_id": x[0], "institution_id": x[1]} for x in qwe]
for d in updict:
    seq(Exposure).filter(Exposure.experimenter_id == d['experimenter_id']).\
        update(d)

app.db.session.bulk_update_mappings(Exposure, updict)
app.db.session.commit()
