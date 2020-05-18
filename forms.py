# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 19:33:29 2020

@author: Alex
"""

from wtforms import Form, StringField, SelectField, DecimalField, SubmitField, \
 IntegerField, BooleanField, SelectMultipleField,validators, FieldList
 
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from app import db
from app.models import Cell_line, Endpoint, Solvent
from wtforms.widgets import html_params
from wtforms_components import FloatIntervalField

def select_multi_checkbox(field, ul_class='', **kwargs):
    kwargs.setdefault('type', 'checkbox')
    field_id = kwargs.pop('id', field.id)
    html = [u'<ul %s style="list-style: none;">' % html_params(id=field_id, class_=ul_class)]
    for value, label, checked in field.iter_choices():
        choice_id = u'%s-%s' % (field_id, value)
        options = dict(kwargs, name=field.name, value=value, id=choice_id)
        if checked:
            options['checked'] = 'checked'
        html.append(u'<li><input %s /> ' % html_params(**options))
        html.append(u'<label for="%s">%s</label></li>' % (field_id, label))
    html.append(u'</ul>')
    return u''.join(html)

class SearchForm(FlaskForm):
    chemical_name = StringField('Chemical name', [validators.Optional(),validators.Length(max=40)])
    cas_number = StringField('CAS-Nr.',[validators.Optional(),validators.Length(max=12)])
    
    endpoint_fields = db.session.query(Endpoint.short_name,Endpoint.full_name).all()
    endpoint = SelectMultipleField('Endpoint',[validators.Optional()],
                                   choices = endpoint_fields,
                                   default = [x[0] for x in endpoint_fields],
                                   widget = select_multi_checkbox)
    
    cell_line_fields = db.session.query(Cell_line.short_name,Cell_line.full_name).all()
    cell_line = SelectMultipleField('Cell line',[validators.Optional()],
                                    choices = cell_line_fields,
                                    default = [x[0] for x in cell_line_fields],
                                    widget = select_multi_checkbox)
    timepoint = IntegerField('Timepoint [h]',[validators.Optional(),validators.NumberRange(min=0,max=10000000)])
    conc_determination = SelectField('Conc. determination',
                                             [validators.Optional()],
                                             choices = [('',''),("me","measured"),("no","nominal")]
                                            )

    logkow_lo = DecimalField("logKow from",[validators.Optional()])
    logkow_hi = DecimalField("logKow to",[validators.Optional()])
    min_replicates = IntegerField('Minimum # replicates',[validators.Optional()])
    solvent = StringField('Solvent',[validators.Optional()])
    fbs = DecimalField('FBS [%]',[validators.Optional()])
    insert = SelectField('Insert',[validators.Optional()],choices = [('',''),('1','yes'),('0','no')])
    passive_dosing = SelectField('Passive dosing',[validators.Optional()],choices = [('',''),('1','yes'),('0','no')])
    dosing = SelectMultipleField('Dosing',[validators.Optional()],
                         choices = [("di","direct"),("in","indirect")],
                         default = ["di","in"],
                         widget=select_multi_checkbox)
    
    submit = SubmitField('Filter')

    
class UploadForm(FlaskForm):
    file = FileField()

    @classmethod
    def refresh(self, file=None):
        form = self(file=file)
        return form
