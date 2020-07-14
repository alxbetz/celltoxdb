# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 15:58:42 2020

@author: Alex
"""

from app.models import Exposure, Chemical, Estimated, Cell_line, Endpoint, \
    Solvent, Medium
from sqlalchemy import or_, and_, asc, desc
import itertools


def composite_query(form, db):
    """
    apply filters from search form 

    Parameters
    ----------
    form : wtform
        query form
    db : flask db object
        flask db connection

    Returns
    -------
    sqlalchemy query
        filtereded query object

    """
    query = db.session.query(Exposure).join(Chemical).join(Estimated) \
        .join(Cell_line).join(Endpoint)

    if (form.chemical_name.data):
        query = query \
            .filter(Chemical.name.ilike('%' + form.chemical_name.data + '%'))

    if (form.cas_number.data):
        query = query.filter(Chemical.cas_number == form.cas_number.data)

    if (form.logkow_lo.data and form.logkow_hi.data):
        lo = form.logkow_lo.data
        hi = form.logkow_hi.data
        est = Chemical.properties[
            'user_corrected_experimental_log_kow'].astext.cast(db.Float)
        exp = Chemical.properties['experimental_log_kow'].astext.cast(db.Float)
        uexp = Chemical.properties['estimated_log_kow'].astext.cast(db.Float)
        query = query.filter(
            or_(and_(est > lo, est < hi), and_(exp > lo, exp < hi),
                and_(uexp > lo, uexp < hi)))

    if (form.cell_line.data):
        query = query.filter(
            Cell_line.full_name.ilike('%' + form.cell_line.data + '%'))


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

#map form fields to filters

filter_mapping = {
    "chemical_name":
    lambda x: Chemical.name.ilike("%" + x + "%"),
    "cas_number":
    lambda x: Chemical.cas_number == x,
    "endpoint":
    lambda x: Endpoint.short_name.in_(tuple(x)),
    "cell_line":
    lambda x: Cell_line.short_name.in_(tuple(x)),
    #"timepoint": lambda x: Exposure.timepoint == x,
    "timepoint":
    lambda x: Exposure.timepoint == int(x)
    if int(x) == 24 else Exposure.timepoint != 24,
    "medium":
    lambda x: Medium.full_name == x if x == "L15" else Medium.full_name != x,
    "conc_determination":
    lambda x: Exposure.conc_determination == x,
    "logkow_lo":
    lambda x: or_(Chemical.experimental_log_kow > x, Chemical.
                  user_corrected_experimental_log_kow > x, Chemical.
                  estimated_log_kow < x),
    "logkow_hi":
    lambda x: or_(Chemical.experimental_log_kow < x, Chemical.
                  user_corrected_experimental_log_kow < x, Chemical.
                  estimated_log_kow < x),
    "min_replicates":
    lambda x: Exposure.replicates >= x,
    "solvent":
    lambda x: Solvent.full_name.ilike("%" + x + "%"),
    "fbs":
    lambda x: Exposure.fbs > 0 if x == '1' else Exposure.fbs == 0,
    "insert":
    lambda x: Exposure.insert == (x == '1'),
    "passive_dosing":
    lambda x: Exposure.passive_dosing == (x == '1'),
    "dosing":
    lambda x: Exposure.dosing.in_(tuple(x))
}


def form_to_filters(form):
    """ Select filter fields that contain values """
    filters = []
    for field in form:
        if field.name == "csrf_token" or field.type == "SubmitField":
            continue

        if field.type == "SelectMultipleField":
            if field.data != field.choices and field.data != [
                    ''
            ] and field.data != ['all']:
                filters.append(filter_mapping[field.name](field.data))
        else:
            if field.data is not None and field.data != "" and field.data != "all":
                filters.append(filter_mapping[field.name](field.data))
    return filters


def apply_filters(query, form):

    filters = form_to_filters(form)
    for f in filters:
        query = query.filter(f)

    return query


#sorting

order_map = {
    'timepoint': Exposure.timepoint,
    'chemical': Chemical.name,
    'cell_line': Cell_line.full_name,
    'endpoint': Endpoint.short_name,
    'ec50': Estimated.ec50,
}

order_dir_map = {'asc': asc, 'desc': desc}

sort_combinations = list(
    itertools.product(order_map.keys(), order_dir_map.keys()))


def apply_ordering(query, colname, direction):
    """ Order query object by column """
    ofun = order_dir_map[direction]
    return query.order_by(ofun(order_map[colname]))
