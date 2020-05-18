# -*- coding: utf-8 -*-
"""
Created on Sun Apr 12 14:13:36 2020

@author: Alex
"""




from app.models import Chemical, Medium, Sample, Exposure, Cell_line \
    , Experimenter, Dose_response, Estimated, Solvent, Endpoint
from fileIO import read_dr, read_estimated
from flask_appbuilder.filemanager import ImageManager
import subprocess
import os
import warnings
import uuid,shutil
from app import db
from app import app

#engine = create_engine("postgresql+psycopg2://utox_admin:iLoveCellLines@/cell_tox_db")


#DBSession = sessionmaker(bind=engine)
#session = DBSession()


fields_record = [
    'plate_size',
    'timepoint',
    'endpoint',
    'passive_dosing',
    'insert',
    'dosing', #direct or indirect
    'conc_determination',
    'solvent',
    'rawfile_hash',
    'id_string',
    'replicates'
    ]


def calc_ec(fname):
    bname = os.path.splitext(os.path.basename(fname))[0]
    print(bname)
    outdir = os.path.join("tmp",bname)
    try:
        os.mkdir(outdir)
    except OSError:
        print ("Directory %s exists" % outdir)
    errPIPE = open(os.path.join(outdir,"stderr.txt"),'w+')
    #sout = subprocess.run(["Rscript",os.path.join("R","fitdr.R"),outdir,os.path.join("..","rawdata",fname)],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    sout = subprocess.Popen(["Rscript",os.path.join("R","fitdr.R"),outdir,fname],stdout=subprocess.PIPE, stderr=errPIPE)
    output, errors = sout.communicate()
    rbname = os.path.join(outdir,bname)
    return {'plot_png_base' : bname + '.png',
        'plot_png_full': rbname + '.png',
     'estimated': rbname + '_estimated.csv',
     'plot_data': rbname + '_plotdata.csv',
    'r_data':  rbname + '.RDS',
        'status': sout
     }


def make_imagename(filename):
    return str(uuid.uuid1()) + "_sep_" + filename

def make_estimated(exposure,ec_out):
    if(ec_out['status'].returncode > 0):
        return None
    est_dict = read_estimated(ec_out['estimated'])
    iname = make_imagename(ec_out['plot_png_base'])
    fcopy = os.path.join(app.config['IMG_UPLOAD_FOLDER'],iname)
    shutil.copy2(ec_out['plot_png_full'],fcopy)
    est_dict['plot_png'] = iname
    binKeys = ['plot_data','r_data']
    for k in binKeys:
        est_dict[k] = open(ec_out[k], 'rb').read()
    est_dict['exposure_id'] = exposure.id
    del est_dict['slope_ci_lower']
    del est_dict['slope_ci_upper']
    
    estimated = Estimated(**est_dict)
    return estimated

def add_record(rec,se,eng):
    
    #check if rawfile has already been adde to the database
    hash_query = se.query(Exposure).filter(Exposure.rawfile_hash == rec['rawfile_hash'])
    if hash_query.count() > 0:
        return False
    
    sample = se.query(Sample).join(Medium).join(Cell_line) \
        .filter(Sample.fbs == rec['fbs']) \
        .filter(Cell_line.short_name == rec['cell_line']) \
        .filter(Medium.short_name==rec['medium']).one_or_none()
        
    if(not sample):
        sample = Sample(cell_line_id = se.query(Cell_line).filter_by(short_name=rec['cell_line']).one().short_name,
                   medium_id = se.query(Medium).filter_by(short_name=rec['medium']).one().short_name,
                   fbs = rec['fbs'])
    se.add(sample)
    
    experimenter = se.query(Experimenter).filter_by(short_name=rec['experimenter']).one()

    to_add = {k: rec[k] for k in fields_record}
    to_add['solvent'] = se.query(Solvent).filter_by(short_name=rec['solvent']).one()
    to_add['endpoint'] =  se.query(Endpoint).filter_by(short_name=rec['endpoint']).one()
    to_add['sample'] = sample
    to_add['experimenter'] = experimenter
    chem = se.query(Chemical).filter_by(cas_number=rec['cas_number']).one_or_none()
    if(chem is None):
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
    
    estimated = make_estimated(exposure,ec_out)
    if estimated is not None:
        
        se.add(estimated)
        se.commit()
    else:
        warnings.warn("Could not calculate EC50 values")
    
    return True

