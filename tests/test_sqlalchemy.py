# -*- coding: utf-8 -*-
"""
Created on Tue May 12 21:41:51 2020

@author: Alex
"""

from app import db
from query_lib import get_database_readable
from app.models import Exposure, Estimated


q = get_database_readable(db)

aa = db.session.query(Exposure,Estimated).filter(Exposure.id == Estimated.exposure_id)

aa.ec50_format_hybrid

