from flask_appbuilder import Model
from flask_appbuilder.models.mixins import ImageColumn
from flask_appbuilder.filemanager import ImageManager
from flask import Markup
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from flask_appbuilder.models.decorators import renders

from app import db

from utils import get_float_prec, format_helper

Boolean = db.Boolean
Float = db.Float
LargeBinary = db.LargeBinary
DateTime = db.DateTime
Date = db.Date


class Chemical(Model):
    __tablename__ = 'chemical'
    id = Column(Integer, primary_key=True, autoincrement=True)
    cas_number = Column(String(20))
    name = Column(String(250))
    estimated_henry_constant = Column(Float)
    estimated_solubility = Column(Float)
    estimated_log_kow = Column(Float)
    experimental_henry_constant = Column(Float)
    experimental_solubility = Column(Float)
    experimental_log_kow = Column(Float)
    user_corrected_experimental_henry_constant = Column(Float)
    user_corrected_experimental_solubility = Column(Float)
    user_corrected_experimental_log_kow = Column(Float)
    molecular_weight = Column(Float)

    def __repr__(self):
        return ' '.join([self.name, self.cas_number])


class Nanomaterial(Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    size = Column(Float)
    treatment = Column(String(200))
    core = Column(String(100))
    coating = Column(String(100))

    def short_rep(self):
        return ' '.join([self.coating[0:3], self.core, "NP"])

    def __repr__(self):
        return ' '.join([self.core, self.coating[0:3], str(self.size)])


class Person(Model):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True, autoincrement=True)
    short_name = Column(String(6))
    full_name = Column(String(50))
    orcid = Column(String(20))
    website = Column(String(255))
    linkedin = Column(String(255))

    def __repr__(self):
        return self.full_name


class Institution(Model):
    __tablename__ = 'institution'
    id = Column(Integer, primary_key=True, autoincrement=True)
    short_name = Column(String(20))
    full_name = Column(String(100))
    country_code = Column(String(2))

    def __repr__(self):
        return self.full_name


class Person_Institution(Model):
    __tablename__ = 'person_institution'
    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey('person.id'))
    institution_id = Column(Integer, ForeignKey('institution.id'))
    start_year = Column(Integer)
    end_year = Column(Integer)
    person = relationship(Person)
    institution = relationship(Institution)


class Cell_line(Model):
    __tablename__ = 'cell_line'
    id = Column(Integer, primary_key=True, autoincrement=True)
    short_name = Column(String(3))
    full_name = Column(String(50))
    organism = Column(String(50))
    tissue = Column(String(30))

    def __repr__(self):
        return self.full_name


class Medium(Model):
    __tablename__ = 'medium'
    id = Column(Integer, primary_key=True, autoincrement=True)
    short_name = Column(String(4),
                        info={
                            'description': '\"mx\" , where x is the medium id',
                            'label': 'Medium ID'
                        })
    full_name = Column(String(100),
                       info={
                           'description': 'Full name of the medium',
                           'label': 'Medium name'
                       })

    def __repr__(self):
        return self.full_name


class Endpoint(Model):
    __tablename__ = 'endpoint'
    id = Column(Integer, primary_key=True, autoincrement=True)
    short_name = Column(String(4))
    full_name = Column(String(20))
    description = Column(String(300))

    def __repr__(self):
        return self.full_name


class Solvent(Model):
    __tablename__ = 'solvent'
    id = Column(Integer, primary_key=True, autoincrement=True)
    short_name = Column(String(4))
    full_name = Column(String(50))

    def __repr__(self):
        return self.full_name


class Experiment_Series(Model):
    __tablename__ = 'experiment_series'
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    description = Column(String(1000))


class Exposure(Model):
    __tablename__ = 'exposure'
    id = Column(Integer, primary_key=True)

    chemical_id = Column(Integer,
                         ForeignKey('chemical.id'),
                         info={'label': 'Chemical'})
    nanomaterial_id = Column(Integer,
                             ForeignKey('nanomaterial.id'),
                             info={'label': 'Nanomaterial'})
    endpoint_id = Column(Integer,
                         ForeignKey('endpoint.id'),
                         info={'label': 'Endpoint'})
    cell_line_id = Column(Integer,
                          ForeignKey('cell_line.id'),
                          info={'label': 'Cell line'})
    medium_id = Column(Integer,
                       ForeignKey('medium.id'),
                       info={'label': 'Medium'})
    fbs = Column(Float,
                 info={
                     'description':
                     'Percent of fetal bovine serum used in medium',
                     'label': 'FBS'
                 })
    timepoint = Column(
        Integer,
        info={
            'description':
            'Time in h between exposure start and endpoint measurement',
            'label': 'Timepoint [h]'
        })
    replicates = Column(Integer,
                        info={
                            'description': 'Number of biological replicates',
                            'label': 'No. of replicates'
                        })
    plate_size = Column(Integer,
                        info={
                            'description': 'Number of wells in plate',
                            'label': 'Plate Size'
                        })
    dosing = Column(String(10),
                    info={
                        'label': 'Dosing',
                        'description': 'direct or indirect'
                    })
    insert = Column(Boolean,
                    info={
                        'description': 'Was an insert used?',
                        'label': 'Insert'
                    })
    passive_dosing = Column(Boolean, info={'label': 'Passive Dosing'})
    solvent_id = Column(Integer,
                        ForeignKey('solvent.id'),
                        info={'label': 'Solvent'})
    id_string = Column(String(200))
    cells_seeded = Column(Integer, info={'label': 'Cells seeded'})
    volume = Column(Float, info={'label': 'Volume'})
    conc_determination = Column(
        String(20),
        info={
            'label':
            'Conc. determination',
            'description':
            'Are the given concentration values nominal or measured?'
        })
    experimenter_id = Column(Integer,
                             ForeignKey('person.id'),
                             info={'label': 'Experimenter'})
    corresponding_author_id = Column(
        Integer,
        ForeignKey('person.id'),
        info={'label': 'Corresponding Investigator'})
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    rawfile_hash = Column(String(40))
    year = Column(Integer, info={'label': 'Year'})
    doi = Column(String(255),
                 info={
                     'label': 'DOI',
                     'description': 'DOI of corresponding publication'
                 })
    series_id = Column(Integer, ForeignKey('experiment_series.id'))
    institution_id = Column(
        Integer,
        ForeignKey('institution.id'),
        info={
            'description': 'Institution where the experiment was performed',
            'label': 'Institution'
        })
    endpoint_group_id = Column(Integer)
    curated = Column(Boolean, default=False)

    endpoint = relationship(Endpoint)
    medium = relationship(Medium)
    cell_line = relationship(Cell_line)
    chemical = relationship(Chemical)
    nanomaterial = relationship(Nanomaterial)
    institution = relationship(Institution)
    experimenter = relationship("Person",
                                foreign_keys="Exposure.experimenter_id",
                                primaryjoin=Person.id == experimenter_id)
    corresponding_author = relationship(
        "Person",
        foreign_keys="Exposure.corresponding_author_id",
        primaryjoin=Person.id == corresponding_author_id)

    solvent = relationship(Solvent)
    estimated = relationship("Estimated",
                             cascade="all, delete-orphan",
                             uselist=False,
                             back_populates="exposure")
    dose_response = relationship("Dose_response",
                                 cascade="all, delete",
                                 backref="exposure",
                                 single_parent=True)
    experiment_series = relationship(Experiment_Series)

    @renders('ec50')
    def ec50_format(self):

        if self.estimated is None:
            return ""
        if not self.estimated.ec50:
            if self.estimated.exceeds_direction:
                precision = get_float_prec(self.estimated.exceeds_value)
                if self.estimated.exceeds_direction == "greater":
                    return "> " + format_helper(self.estimated.exceeds_value,
                                                precision)
                else:
                    return "< " + format_helper(self.estimated.exceeds_value,
                                                precision)
            else:
                return ""
        precision = get_float_prec(self.estimated.ec50)
        return Markup("<b>"+ format_helper(self.estimated.ec50,precision) + "</b>" +\
                      ' (' + format_helper(self.estimated.ec50_ci_lower,precision) + \
                      '-' + format_helper(self.estimated.ec50_ci_upper,precision) +
                      ')')


class Dose_response(Model):
    __tablename__ = 'dose_response'
    exposure_id = Column(Integer, ForeignKey('exposure.id'), primary_key=True)
    replicate = Column(Integer, primary_key=True)
    concentration = Column(Float, primary_key=True)
    effect = Column(Float)


class Estimated(Model):
    __tablename__ = 'estimated'
    exposure_id = Column(Integer, ForeignKey('exposure.id'), primary_key=True)
    ec50 = Column(Float)
    ec50_ci_upper = Column(Float)
    ec50_ci_lower = Column(Float)
    ec10 = Column(Float)
    ec10_ci_upper = Column(Float)
    ec10_ci_lower = Column(Float)
    ntc = Column(Float)
    slope = Column(Float)
    confidence_level = Column(Float)
    exceeds_direction = Column(String(10))
    exceeds_value = Column(Float)
    plot_png = Column(
        ImageColumn(size=(600, 600, True), thumbnail_size=(60, 60, True)))
    r_data = Column(LargeBinary)
    plot_data = Column(LargeBinary)
    exposure = relationship(Exposure,
                            back_populates="estimated",
                            cascade="all, delete")

    @renders('ec50')
    def ec50_format(self):

        if not self.ec50:
            if self.exceeds_direction:
                precision = get_float_prec(self.exceeds_value)
                if self.exceeds_direction == "greater":
                    return "> " + format_helper(self.exceeds_value, precision)
                else:
                    return "< " + format_helper(self.exceeds_value, precision)
            else:
                return ""

        precision = get_float_prec(self.ec50)
        return Markup("<b>"+ format_helper(self.ec50,precision) + "</b>" +\
                      ' (' + format_helper(self.ec50_ci_lower,precision) + \
                      '-' + format_helper(self.ec50_ci_upper,precision) +
                      ')')

    def dr_img(self):

        im = ImageManager()
        if self.plot_png:
            return Markup('<img src="' + im.get_url(self.plot_png) +\
              '" alt="Dose response plot" >')


class Chemical_xref(Model):
    __tablename__ = 'predicted'
    chemical_id = Column(Integer, ForeignKey('chemical.id'), primary_key=True)
    database = Column(String(20), primary_key=True)
    database_id = Column(String(40))
