from flask_appbuilder import Model
from flask_appbuilder.models.mixins import ImageColumn
from flask_appbuilder.filemanager import ImageManager
from flask import Markup
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from sqlalchemy.orm import backref
from flask_appbuilder.models.decorators import renders

from app import db

from utils import get_float_prec


Boolean = db.Boolean
Float = db.Float
LargeBinary = db.LargeBinary
DateTime = db.DateTime
Date = db.Date



class Chemical(Model):
    __tablename__ = 'chemical'
    id = Column(Integer, primary_key=True,autoincrement=True)
    cas_number = Column(String(20))
    name = Column(String(250))
    estimated_henry_constant = Column(Float)
    estimated_solubility  = Column(Float)
    estimated_log_kow  = Column(Float)
    experimental_henry_constant = Column(Float)
    experimental_solubility  = Column(Float)
    experimental_log_kow  = Column(Float)
    user_corrected_experimental_henry_constant = Column(Float)
    user_corrected_experimental_solubility  = Column(Float)
    user_corrected_experimental_log_kow  = Column(Float)
    molecular_weight = Column(Float)

    
    def __repr__(self):
        return self.name

class Experimenter(Model):
    __tablename__ = 'experimenter'
    id = Column(Integer, primary_key=True,autoincrement=True)
    short_name = Column(String(3))
    full_name = Column(String(50))
    
    def __repr__(self):
        return self.full_name
    
class Cell_line(Model):
    __tablename__ = 'cell_line'
    short_name = Column(String(3),primary_key=True,)
    full_name = Column(String(50))
    organism = Column(String(50))
    tissue = Column(String(30))
    
    def __repr__(self):
        return self.full_name
    
class Medium(Model):
    __tablename__ = 'medium'
    short_name = Column(String(4),primary_key=True)
    full_name = Column(String(100))
    
    def __repr__(self):
        return self.full_name

    
class Sample(Model):
    __tablename__ = 'sample'
    id = Column(Integer, primary_key=True,autoincrement=True)
    cell_line_id = Column(String(4), ForeignKey('cell_line.short_name'))
    cell_line = relationship(Cell_line)
    medium_id = Column(String(4), ForeignKey('medium.short_name'))
    fbs = Column(Float)
    medium = relationship(Medium)
    
    def __repr__(self):
        return self.cell_line.full_name + ":" + self.medium.full_name + ":FBS" + str(self.fbs)

class Endpoint(Model):
    __tablename__ = 'endpoint'
    short_name = Column(String(4), primary_key=True)
    full_name = Column(String(20))
    
    def __repr__(self):
        return self.full_name
    
class Solvent(Model):
    __tablename__ = 'solvent'
    short_name = Column(String(4), primary_key=True)
    full_name = Column(String(50))
    
    def __repr__(self):
        return self.full_name
    
class Exposure(Model):
    __tablename__ = 'exposure'
    id = Column(Integer, primary_key=True)
    sample_id = Column(Integer, ForeignKey('sample.id'))
    chemical_id = Column(Integer, ForeignKey('chemical.id'))
    endpoint_id = Column(String(4), ForeignKey('endpoint.short_name'))
    timepoint = Column(Integer)
    replicates = Column(Integer)
    plate_size = Column(Integer)
    dosing = Column(String(10))
    insert = Column(Boolean)
    passive_dosing = Column(Boolean)
    solvent_id = Column(String(20),ForeignKey('solvent.short_name'))
    id_string = Column(String(200))
    cells_seeded = Column(Integer)
    volume = Column(Float)
    conc_determination = Column(String(20))
    experimenter_id = Column(Integer, ForeignKey('experimenter.id'))
    date_created = Column(DateTime,default=datetime.datetime.utcnow)
    date_exposure = Column(Date)
    rawfile_hash = Column(String(40))
    year = Column(Integer)
    
    endpoint = relationship(Endpoint)
    sample = relationship(Sample)
    chemical = relationship(Chemical)
    experimenter = relationship(Experimenter)
    solvent = relationship(Solvent)
    estimated = relationship("Estimated", cascade="all,delete",uselist=False,
                             back_populates="exposure")
    
class Nanoparticle(Model):
    id = Column(Integer,primary_key = True)
    size = Column(Float)
    treatment = Column(String(200))
    core = Column(String(50))
    
    
    # ec50 = association_proxy('estimated', 'ec50')
    # ec50_ci_lower = association_proxy('estimated', 'ec50_ci_lower') 
    # ec50_ci_upper = association_proxy('estimated', 'ec50_ci_upper') 
    
    # @hybrid_property
    # def ec50_format_hybrid(self):
       
    #     if self.estimated is None:
    #         return ""
    #     precision =  get_float_prec(self.ec50)
    #     return Markup("<b>{:.{}f}</b>".format(self.ec50, precision + 1 ) +\
    #                   ' (' + "{:.{}f}".format( self.ec50_ci_lower, precision+1)+ \
    #                   '-' + "{:.{}f}".format( self.ec50_ci_upper, precision+1)+
    #                   ')')
    
    @renders('ec50')
    def ec50_format(self):
       
        if self.estimated is None:
            return ""
        precision =  get_float_prec(self.estimated.ec50)
        return Markup("<b>{:.{}f}</b>".format(self.estimated.ec50, precision + 1 ) +\
                      ' (' + "{:.{}f}".format( self.estimated.ec50_ci_lower, precision+1)+ \
                      '-' + "{:.{}f}".format( self.estimated.ec50_ci_upper, precision+1)+
                      ')')

    
    
class Dose_response(Model):
    __tablename__ = 'dose_response'
    exposure_id = Column(Integer, ForeignKey('exposure.id'), primary_key=True)
    replicate = Column(Integer, primary_key = True)
    concentration = Column(Float,primary_key=True)
    effect = Column(Float)
    exposure = relationship(Exposure,backref=backref("dose_response", cascade="all,delete-orphan"))
    
    




        

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
    plot_png = Column(ImageColumn(size=(600, 600, True), thumbnail_size=(60, 60, True)))
    r_data = Column(LargeBinary)
    plot_data = Column(LargeBinary)
    exposure = relationship(Exposure, back_populates="estimated")

    @renders('ec50')
    def ec50_format(self):
        precision =  get_float_prec(self.ec50)
        return Markup("<b>{:.{}f}</b>".format( self.ec50, precision + 1 ) +\
                      ' (' + "{:.{}f}".format( self.ec50_ci_lower, precision+1)+ \
                      '-' + "{:.{}f}".format( self.ec50_ci_upper, precision+1)+
                      ')')
                         
    
    def dr_img(self):

        im = ImageManager()
        if self.plot_png:
            return Markup('<img src="' + im.get_url(self.plot_png) +\
              '" alt="Dore response plot" >')
                



class Chemical_xref(Model):
    __tablename__ = 'predicted'
    chemical_id = Column(Integer, ForeignKey('chemical.id'), primary_key=True)
    database = Column(String(20), primary_key=True)
    database_id = Column(String(40))
    

 
