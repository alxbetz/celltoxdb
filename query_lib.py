from app.models import Exposure, Chemical, Estimated, Sample, Cell_line, Endpoint, Solvent, Experimenter, Medium
from utils import get_float_prec


def get_database_readable(db):
    querydb = db.session.query(Exposure,Estimated) \
      .filter(Exposure.id == Estimated.exposure_id) \
      .join(Chemical) \
      .join(Sample) \
      .join(Cell_line) \
      .join(Medium) \
      .join(Solvent) \
      .join(Endpoint) \
      .join(Experimenter) \
    .with_entities(
    Exposure.id.label("exposure_id"),
    Chemical.name.label("chemical_name"),
    Chemical.cas_number,
    Chemical.user_corrected_experimental_log_kow,
    Chemical.experimental_log_kow,
    Chemical.estimated_log_kow,
    Chemical.user_corrected_experimental_solubility,
    Chemical.experimental_solubility,
    Chemical.estimated_solubility,
    Chemical.user_corrected_experimental_henry_constant,
    Chemical.experimental_henry_constant,
    Chemical.estimated_henry_constant,
    Chemical.molecular_weight,
    Cell_line.full_name.label("cell_line"),
    Endpoint.full_name.label("endpoint"),
    Exposure.timepoint,
    Exposure.dosing,
    Exposure.insert,
    Exposure.passive_dosing,
    Exposure.plate_size,
    Solvent.full_name.label("solvent"),
    Exposure.conc_determination,
    Medium.full_name.label("medium"),
    Sample.fbs,
    Experimenter.full_name.label("experimenter"),
    Estimated.ec50,
    Estimated.ec50_ci_lower,
    Estimated.ec50_ci_upper,
    Estimated.ec10,
    Estimated.ec10_ci_lower,
    Estimated.ec10_ci_upper,
    Estimated.ntc)
    return querydb

pretty_names = {
    "chemical_name" : "Chemical",
    "cell_line" : "Cell line",
    "timepoint" : "Timepoint [h]",
    "endpoint" : "Endpoint",
    "ec50" : "EC50 [mg/L]"
    }
from sqlalchemy.orm import joinedload,contains_eager

def get_exposure_eager(db):
    q = db.session.query(Exposure,Estimated) \
      .filter(Exposure.id == Estimated.exposure_id) \
      .join(Chemical) \
      .join(Sample) \
      .join(Cell_line) \
      .join(Endpoint) \
      .join(Medium)
      
    return q



import pandas as pd
def get_database_stats(db):
    q = get_database_readable(db)
    df = pd.DataFrame(q)
    

    return {'nExperiments' : q.count() ,
            'cell_line_table' : df[["exposure_id","cell_line"]].groupby("cell_line").count(),
            'chemical_table' : df[["exposure_id","chemical_name","cas_number"]].groupby(["cas_number","chemical_name"]).count()
            }