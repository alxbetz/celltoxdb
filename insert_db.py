# -*- coding: utf-8 -*-
"""
Created on Sun Apr 12 14:13:36 2020

@author: Alex
"""

from app.models import Chemical, Medium, Exposure, Cell_line \
    , Person, Estimated, Solvent, Endpoint, Nanomaterial
from fileIO import  read_estimated

import subprocess
import os
import warnings
import uuid, shutil

from app import app

fields_record = [
    'plate_size',
    'timepoint',
    'endpoint',
    'passive_dosing',
    'insert',
    'dosing',  #direct or indirect
    'conc_determination',
    'solvent',
    'rawfile_hash',
    'id_string',
    'replicates'
]


def calc_ec(fname):
    """
    

    Parameters
    ----------
    fname : string
        filename of dose response values, first column must be concentration

    Returns
    -------
    dict
        output file names and R call status flag

    """
    bname = os.path.splitext(os.path.basename(fname))[0]
    print(bname)
    outdir = os.path.join("tmp", bname)
    try:
        os.mkdir(outdir)
    except OSError:
        print("Directory %s exists" % outdir)
    errPIPE = open(os.path.join(outdir, "stderr.txt"), 'w+')
    
    rcall = " ".join(
        ["Rscript",
         os.path.join("R", "fitdr.R"), outdir, fname, "delta"])
    sout = subprocess.Popen(
        ["Rscript",
         os.path.join("R", "fitdr.R"), outdir, fname, "delta"],
        stdout=subprocess.PIPE,
        stderr=errPIPE)

    output, errors = sout.communicate()
    rbname = os.path.join(outdir, bname)
    return {
        'rcall': rcall,
        'plot_png_base': bname + '.png',
        'plot_png_full': rbname + '.png',
        'estimated': rbname + '_estimated.csv',
        'plot_data': rbname + '_plotdata.csv',
        'r_data': rbname + '.RDS',
        'status': sout
    }


def make_imagename(filename):
    """ Generate a unique name for an image"""
    return str(uuid.uuid1()) + "_sep_" + filename


def make_estimated(exposure, ec_out):
    """
    

    Parameters
    ----------
    exposure : TYPE
        DESCRIPTION.
    ec_out : TYPE
        DESCRIPTION.

    Returns
    -------
    estimated : TYPE
        DESCRIPTION.

    """
    if (ec_out['status'].returncode > 0):
        return None
    est_dict = read_estimated(ec_out['estimated'])
    iname = make_imagename(ec_out['plot_png_base'])
    fcopy = os.path.join(app.config['IMG_UPLOAD_FOLDER'], iname)
    shutil.copy2(ec_out['plot_png_full'], fcopy)
    est_dict['plot_png'] = iname

    # if no EC50 values could be calculated, the slope CIs dont need to be removed
    if 'exceeds_direction' not in est_dict.keys():
        binKeys = ['plot_data', 'r_data']
        for k in binKeys:
            est_dict[k] = open(ec_out[k], 'rb').read()
        del est_dict['slope_ci_lower']
        del est_dict['slope_ci_upper']

    est_dict['exposure_id'] = exposure.id
    estimated = Estimated(**est_dict)
    return estimated


def check_rawfile(hash_string, se):
    hash_query = se.query(Exposure).filter(
        Exposure.rawfile_hash == hash_string)
    warnings.warn("Rawfile was already added to the database")
    if hash_query.count() > 0:
        return False
    else:
        return True


def add_record(rec, se, eng):
    """
    

    Parameters
    ----------
    rec : dict
        DESCRIPTION.
    se : flask session object
        The current database session
    eng : database engine object
        DESCRIPTION.

    Returns
    -------
    bool
        DESCRIPTION.

    """

    #check if rawfile has already been added to the database already
    file_check = check_rawfile(rec['rawfile_hash'], se)
    if not file_check:
        return False

    cell_line = se.query(Cell_line).filter(
        Cell_line.short_name == rec['cell_line']).one_or_none()
    medium = se.query(Medium).filter(
        Medium.short_name == rec['medium']).one_or_none()

    experimenter = se.query(Person).filter_by(
        short_name=rec['experimenter']).one()

    to_add = {k: rec[k] for k in fields_record}
    to_add['solvent'] = se.query(Solvent).filter_by(
        short_name=rec['solvent']).one()
    to_add['endpoint'] = se.query(Endpoint).filter_by(
        short_name=rec['endpoint']).one()
    to_add['medium'] = medium
    to_add['cell_line'] = cell_line
    to_add['experimenter'] = experimenter
    chem = se.query(Chemical).filter_by(
        cas_number=rec['cas_number']).one_or_none()
    if chem is None:
        if rec['cas_number'].find("nano") == 0:
            nano_id = int(rec['cas_number'].strip("nano"))
            nano_rec = se.query(Nanomaterial).filter(
                Nanomaterial.id == nano_id).one_or_none()
            to_add['nanomaterial'] = nano_rec
        else:
            return False
    else:
        to_add['chemical'] = chem

    exposure = Exposure(**to_add)

    #after the commit exposure.id gets a value
    se.add(exposure)
    se.commit()

    rec['raw_data']['exposure_id'] = exposure.id
    rec['raw_data'].to_sql("dose_response",
                           eng,
                           if_exists='append',
                           schema='public',
                           index=False,
                           chunksize=500)

    ec_out = calc_ec(rec['filename'])

    estimated = make_estimated(exposure, ec_out)
    if estimated is not None:

        se.add(estimated)
        se.commit()
    else:
        warnings.warn("Could not calculate EC50 values")

    return True


def create_exposure(rec, se):
    """
    

    Parameters
    ----------
    rec : TYPE
        DESCRIPTION.
    se : TYPE
        DESCRIPTION.

    Returns
    -------
    exposure : TYPE
        DESCRIPTION.

    """

    for k, v in rec.items():
        if isinstance(rec[k], str) and rec[k] == 'None':
            rec[k] = None
        elif k.endswith("_id"):
            rec[k] = int(rec[k])
    #get set of fields which are columns in the database
    ifields = set(Exposure.__dict__.keys()).intersection(set(rec.keys()))
    to_add = {k: rec[k] for k in ifields}
    exposure = Exposure(**to_add)
    se.add(exposure)
    se.commit()
    return exposure


def add_record_rawdata(rec, se, eng):
    """
    

    Parameters
    ----------
    rec : dict
        DESCRIPTION.
    se : flask session object
        The current database session
    eng : database engine object
        DESCRIPTION.

    Returns
    -------
    bool
        DESCRIPTION.

    """

    #check if rawfile has already been added to the database
    file_check = check_rawfile(rec['rawfile_hash'], se)
    if not file_check:
        return False

    exposure = create_exposure(rec, se)

    rec['raw_data']['exposure_id'] = exposure.id
    rec['raw_data'].to_sql("dose_response",
                           eng,
                           if_exists='append',
                           schema='public',
                           index=False,
                           chunksize=500)

    ec_out = calc_ec(rec['filename'])

    estimated = make_estimated(exposure, ec_out)
    if estimated is not None:

        se.add(estimated)
        se.commit()
    else:
        warnings.warn("Could not calculate EC50 values")

    return exposure


def add_record_norawdata(rec, se):
    """
    

    Parameters
    ----------
    rec : TYPE
        DESCRIPTION.
    se : TYPE
        DESCRIPTION.

    Returns
    -------
    exposure : TYPE
        DESCRIPTION.

    """

    exposure = create_exposure(rec, se)
    rec['exposure_id'] = exposure.id
    ifields = set(Estimated.__dict__.keys()).intersection(set(rec.keys()))
    estimated_dict = {k: rec[k] for k in ifields}
    estimated = Estimated(**estimated_dict)
    se.add(estimated)
    se.commit()

    return exposure
