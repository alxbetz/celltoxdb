# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 15:58:42 2020

@author: Alex
"""

from app.models import Exposure, Chemical, Estimated, Cell_line, Sample, Endpoint, Solvent, Medium
from sqlalchemy import or_, and_

def composite_query(form,db):
    query = db.session.query(Exposure).join(Chemical).join(Estimated) \
        .join(Sample).join(Cell_line).join(Endpoint)
        
    
    if(form.chemical_name.data):
        query = query \
            .filter(Chemical.name.ilike('%' + form.chemical_name.data + '%'))
    
    if(form.cas_number.data):
        query = query.filter(Chemical.cas_number == form.cas_number.data)
    
    if(form.logkow_lo.data and form.logkow_hi.data):
        lo = form.logkow_lo.data
        hi = form.logkow_hi.data
        est = Chemical.properties['user_corrected_experimental_log_kow'].astext.cast(db.Float)
        exp = Chemical.properties['experimental_log_kow'].astext.cast(db.Float)
        uexp =Chemical.properties['estimated_log_kow'].astext.cast(db.Float)
        query = query.filter(
            or_(
                and_(est > lo,est<hi),
                and_(exp > lo,exp<hi),
                and_(uexp > lo,uexp<hi)
            )
        )
                             
    if(form.cell_line.data):
         query = query.filter(Cell_line.full_name.ilike('%' + form.cell_line.data + '%'))

    
    return query \
        .with_entities(
        Exposure.id,
        Chemical.name,
        Cell_line.full_name,
        Endpoint.full_name,
        Exposure.timepoint,
        Estimated.ec50,
        Estimated.ec50_ci_lower,
        Estimated.ec50_ci_upper)


filter_mapping = {
    "chemical_name": lambda x: Chemical.name.ilike("%" + x + "%"),
    "cas_number": lambda x: Chemical.cas_number == x,
    "endpoint" : lambda x: Exposure.endpoint_id.in_(tuple(x)),
    "cell_line" : lambda x: Cell_line.short_name.in_(tuple(x)),
    #"timepoint": lambda x: Exposure.timepoint == x,
    "timepoint": lambda x: Exposure.timepoint == int(x) if int(x) == 24 else Exposure.timepoint != 24,
    "medium" : lambda x: Medium.full_name == x if x =="L15" else Medium.full_name!= x ,
    "conc_determination": lambda x: Exposure.conc_determination == x,
    "logkow_lo": lambda x: or_(Chemical.experimental_log_kow > x,
                               Chemical.user_corrected_experimental_log_kow > x,
                               Chemical.estimated_log_kow < x),
    "logkow_hi": lambda x: or_(Chemical.experimental_log_kow < x,
                               Chemical.user_corrected_experimental_log_kow < x,
                               Chemical.estimated_log_kow < x),
    "min_replicates": lambda x: Exposure.replicates >= x,
    "solvent": lambda x: Solvent.full_name.ilike("%" + x + "%"),
    "fbs": lambda x: Sample.fbs > 0 if x == '1' else Sample.fbs == 0,
    "insert": lambda x: Exposure.insert == (x == '1'),
    "passive_dosing": lambda x: Exposure.passive_dosing == (x == '1'),
    "dosing": lambda x: Exposure.dosing.in_(tuple(x))
    }
    
def form_to_filters(form):
    filters = []
    for field in form:
        if field.name == "csrf_token" or field.type  == "SubmitField":
            continue
        
        if field.type == "SelectMultipleField":
            if field.data != field.choices and field.data != [''] and field.data != ['all']:
                filters.append(filter_mapping[field.name](field.data))
        else:
            if field.data is not None and field.data != "" and field.data != "all":
                filters.append(filter_mapping[field.name](field.data))
    return filters

def apply_filters(query,form):

    filters = form_to_filters(form)
    for f in filters:
        query = query.filter(f)
        
    return query


    
    # def validate(self):
    #     if not super(SearchForm, self).validate():
    #         return False
    #     if not self.chemical_name.data and not \
    #     self.cas_number.data and not self.cell_line.data \
    #         and not (self.logkow_hi.data and self.logkow_lo.data):
    #         msg = 'At least one search field must be filled'
    #         self.chemical_name.append(msg)
    #         self.cas_number.append(msg)
    #         self.cell_line.append(msg)
    #         return False
    #     return True

