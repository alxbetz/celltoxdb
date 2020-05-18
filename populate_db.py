# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 18:40:12 2020

@author: Alex
"""
from app import db
from insert_db import add_record
from fileIO import read_dr

import os

files = list(filter(lambda x: not x.startswith('.~lock'),os.listdir('..\\rawdata')))
# fname  = files[1]
# dat = read_dr('..\\rawdata\\' + fname)


data = [read_dr('..\\rawdata\\' + fname,verbose = True) for fname in files]

add_record(data[0],db.session,db.engine)

for d in data:
    try:
        add_record(d,db.session,db.engine)
    except:
        pass