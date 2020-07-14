from app.models import Exposure, Chemical, Estimated, Cell_line, Endpoint, \
    Solvent, Person, Medium, Nanomaterial, Institution
from utils import get_float_prec
import pandas as pd


def get_database_readable(db):
    """
    

    Parameters
    ----------
    db : sqlalchemy database connections
        DESCRIPTION.

    Returns
    -------
    querydb : TYPE
        DESCRIPTION.

    """
    e_person = db.aliased(Person)
    ca_person = db.aliased(Person)

    querydb = db.session.query(Exposure) \
      .outerjoin(Estimated) \
      .join(Chemical) \
      .outerjoin(Cell_line) \
      .join(Medium) \
      .join(Solvent) \
      .join(Endpoint) \
      .outerjoin(Institution) \
      .outerjoin(e_person,Exposure.experimenter_id == e_person.id) \
      .outerjoin(ca_person,Exposure.corresponding_author_id == ca_person.id) \
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
    Exposure.fbs,
    Institution.full_name,
    e_person.full_name.label("experimenter"),
    ca_person.full_name.label("corresponding_researcher"),
    Estimated.ec50,
    Estimated.ec50_ci_lower,
    Estimated.ec50_ci_upper,
    Estimated.ec10,
    Estimated.ec10_ci_lower,
    Estimated.ec10_ci_upper,
    Estimated.ntc)
    return querydb


pretty_names = {
    "chemical_name": "Chemical",
    "cell_line": "Cell line",
    "timepoint": "Timepoint [h]",
    "endpoint": "Endpoint",
    "ec50": "EC50 [mg/L]"
}


def get_exposure_eager(db):

    e_person = db.aliased(Person)
    ca_person = db.aliased(Person)

    q = db.session.query(Exposure) \
      .outerjoin(Estimated) \
      .outerjoin(Chemical) \
      .outerjoin(Nanomaterial) \
      .outerjoin(Cell_line) \
      .join(Medium) \
      .join(Endpoint) \
      .outerjoin(e_person,Exposure.experimenter_id == e_person.id) \
      .outerjoin(ca_person,Exposure.corresponding_author_id == ca_person.id)

    return q




def get_database_stats(db):
    q = get_database_readable(db)
    df = pd.DataFrame(q)

    return {
        'nExperiments':
        q.count(),
        'cell_line_table':
        df[["exposure_id", "cell_line"]].groupby("cell_line").count(),
        'chemical_table':
        df[["exposure_id", "chemical_name",
            "cas_number"]].groupby(["cas_number", "chemical_name"]).count()
    }
