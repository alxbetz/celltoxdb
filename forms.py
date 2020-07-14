# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 19:33:29 2020

@author: Alex
"""

from wtforms import StringField, SelectField, DecimalField, SubmitField, \
 IntegerField, BooleanField, SelectMultipleField,validators, FloatField

from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from app import db

from wtforms.widgets import html_params
from wtforms.validators import ValidationError

from wtforms_alchemy import ModelForm,  ModelFormField

from app.models import Exposure,Chemical,Person,Cell_line,Medium,Endpoint, \
    Institution, Solvent



def select_multi_checkbox(field, ul_class='', **kwargs):
    kwargs.setdefault('type', 'checkbox')
    field_id = kwargs.pop('id', field.id)
    html = [
        u'<ul %s style="list-style: none;">' %
        html_params(id=field_id, class_=ul_class)
    ]
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
    chemical_name = StringField(
        'Chemical name', [validators.Optional(),
                          validators.Length(max=40)])
    cas_number = StringField(
        'CAS-Nr.', [validators.Optional(),
                    validators.Length(max=12)])

    #endpoint_fields = db.session.query(Endpoint.short_name,Endpoint.full_name).all()
    endpoint_fields = [('AB', 'metabolic activity (alamarBlue or PrestoBlue)'),
                       ('CF', 'cell membrane integrity (CFDA-AM)'),
                       ('NR', 'lysosomal membrane integrity (NeutralRed)')]
    endpoint = SelectMultipleField('Endpoint', [validators.Optional()],
                                   choices=endpoint_fields,
                                   default=[x[0] for x in endpoint_fields],
                                   widget=select_multi_checkbox)

    cell_line_fields = db.session.query(Cell_line.short_name,
                                        Cell_line.full_name).all()
    cell_line = SelectMultipleField('Cell line', [validators.Optional()],
                                    choices=cell_line_fields,
                                    default=[x[0] for x in cell_line_fields],
                                    widget=select_multi_checkbox)
    #timepoint = IntegerField('Timepoint [h]',[validators.Optional(),validators.NumberRange(min=0,max=10000000)])
    timepoint = SelectField('Timepoint [h]', [validators.Optional()],
                            choices=[('all', 'all'), ('24', '24h'),
                                     ('0', 'other')])

    medium = SelectField('Medium', [validators.Optional()],
                         choices=[('all', 'all'), ('L15/ex', 'L15/ex'),
                                  ('L15_other', 'L15 other')])

    conc_determination = SelectField('Conc. determination',
                                     [validators.Optional()],
                                     choices=[('all', 'all'),
                                              ("me", "measured"),
                                              ("no", "nominal")])

    logkow_lo = DecimalField("logKow from", [validators.Optional()])
    logkow_hi = DecimalField("logKow to", [validators.Optional()])
   
    min_replicates = IntegerField('Minimum # replicates',
                                  [validators.Optional()])
    solvent = StringField('Solvent', [validators.Optional()])
    fbs = SelectField('FBS', [validators.Optional()],
                      choices=[('all', 'all'), ('1', 'yes'), ('0', 'no')])
    dosing = SelectMultipleField('Dosing', [validators.Optional()],
                                 choices=[("di", "direct"),
                                          ("in", "indirect")],
                                 default=["di", "in"],
                                 widget=select_multi_checkbox)
    passive_dosing = SelectField('Passive dosing', [validators.Optional()],
                                 choices=[('all', 'all'), ('1', 'yes'),
                                          ('0', 'no')])

    insert = SelectField('Cell culture insert', [validators.Optional()],
                         choices=[('all', 'all'), ('1', 'yes'), ('0', 'no')])

    submit = SubmitField('Filter')


class UploadForm(FlaskForm):
    file = FileField()

    @classmethod
    def refresh(self, file=None):
        form = self(file=file)
        return form


def get_choices(db, sqla_model):
    fields = db.session.query(sqla_model.id, sqla_model).all()
    fields_str = [(str(k), str(v)) for k, v in fields]
    # fields_str.insert(0,('None',''))
    return sorted(fields_str, key=lambda x: x[1])


import sqlalchemy as sa
import flask_appbuilder
i = sa.inspect(Exposure)

COL_TO_RELOBJ = {}
for k, v in i.relationships.items():
    if (v.direction == sa.orm.interfaces.MANYTOONE):
        COL_TO_RELOBJ.update({list(v.local_columns)[0].name: v.argument})

COL_TO_FIELD = {
    sa.types.Integer: IntegerField,
    sa.types.Float: FloatField,
    sa.types.String: StringField,
    sa.types.Boolean: BooleanField
}


def substance_validator(form, field):
    a = form.chemical_id.data == "None"
    b = form.nanomaterial_id.data == "None"
    if ((a and b) or not (a or b)):
        raise ValidationError(
            'Either chemical or nanomaterial must be specified.')


def estimated_validator(form, field):
    fi = form.file.data is None

    ec = form.ec50.data is None
    error = form.error_value.data is None
    rep = form.replicates.data is None
    nconc = form.nconcentrations.data is None

    b = ec and rep and nconc and error
    if ((fi and b) or not (fi or b)):
        raise ValidationError(
            'Either a raw file or the EC50 value, including error and number of data points need to be supplied'
        )


def makeUploadSingleForm(**kwargs):
    """
    

    Parameters
    ----------
    **kwargs : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    include_fields = [
        "nanomaterial_id", "chemical_id", "endpoint_id", "cell_line_id",
        "timepoint", "medium_id", "conc_determination", "solvent_id", "fbs",
        "dosing", "passive_dosing", "insert", "plate_size", "volume",
        "experimenter_id", "corresponding_author_id", "institution_id", "year"
    ]

    class UploadSingleForm(FlaskForm):
        @classmethod
        def refresh(self, file=None):
            form = self(file=file)
            return form
    for fieldName in include_fields:
        colType = Exposure.__dict__[fieldName].type
        fieldType = COL_TO_FIELD[type(colType)]
        column = Exposure.__dict__[fieldName]
        if "label" in column.info.keys():
            label = column.info['label']
        else:
            label = fieldName

        if len(column.foreign_keys) > 0:

            relObj = COL_TO_RELOBJ[fieldName]
            # handle the case that relObj is a class resolver and not a class
            if not isinstance(
                    relObj, flask_appbuilder.models.sqla.ModelDeclarativeMeta):
                relObj = relObj()
            choices = get_choices(db, relObj)
            if fieldName == 'chemical_id' or fieldName == 'nanomaterial_id':
                choices.insert(0, ('None', ''))
                field = SelectField(
                    label=label,
                    choices=choices,
                    validators=[validators.Optional(), substance_validator])
            else:
                field = SelectField(label=label, choices=choices)
        elif fieldName == "dosing":
            field = SelectField(label=label,
                                choices=[("di", "indirect"), ("in", "direct")])
        elif fieldName == 'conc_determination':
            field = SelectField(label=label,
                                choices=[("no", "nominal"),
                                         ("me", "measured")])
        else:
            field = fieldType(label=label)

        setattr(UploadSingleForm, fieldName, field)

    setattr(UploadSingleForm, "file",
            FileField(validators=[validators.Optional(), estimated_validator]))
    setattr(
        UploadSingleForm, "error_type",
        SelectField(label="Error type",
                    choices=[("ci", "95% Confidence Interval"),
                             ('std', 'Standard Deviation')],
                    validators=[validators.Optional()]))
    setattr(
        UploadSingleForm, "ec50",
        FloatField(label='EC50',
                   validators=[validators.Optional(), estimated_validator]))
    setattr(
        UploadSingleForm, "error_value",
        FloatField(label='Value of error',
                   validators=[validators.Optional(), estimated_validator]))
    setattr(
        UploadSingleForm, "replicates",
        IntegerField(label='number of biological replicates',
                     validators=[validators.Optional(), estimated_validator]))
    setattr(
        UploadSingleForm, "nconcentrations",
        IntegerField(label='number of concentrations tested',
                     validators=[validators.Optional(), estimated_validator]))

    return UploadSingleForm(**kwargs)





class ChemicalForm(ModelForm):
    class Meta:
        model = Chemical


class CellLineField(ModelForm):
    class Meta:
        model = Cell_line


class MediumForm(ModelForm):
    class Meta:
        model = Medium


class PersonForm(ModelForm):
    class Meta:
        model = Person


class EndpointForm(ModelForm):
    class Meta:
        model = Endpoint


class SolventForm(ModelForm):
    class Meta:
        model = Solvent


class ExposureForm(ModelForm):
    class Meta:
        model = Exposure
        
class InstitutionForm(ModelForm):
    class Meta:
        model = Institution

    chemical = ModelFormField(ChemicalForm)
    cell_line = ModelFormField(CellLineField)
    endpoint = ModelFormField(EndpointForm)
    medium = ModelFormField(MediumForm)
    solvent = ModelFormField(SolventForm)
    experimenter = ModelFormField(PersonForm)
    corresponding_author = ModelFormField(PersonForm)
