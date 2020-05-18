# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 17:27:10 2020

@author: Alex
"""
import ntpath
import os
import pandas as pd
import hashlib


fields = [
    'cell_line',
    'experimenter',
    'plate_size',
    'timepoint',
    'endpoint',
    'medium',
    'fbs',
    'insert_passive_dosing',
    'dosing', #direct or indirect
    'conc_determination',
    'solvent',
    'cas_number'
    ]

fields_ml = fields[:7] + ["volume"] + fields[7:]


def parse_file_string(s):
    s = ntpath.basename(s)
    fname = s.split('.')
    has_ml = True if "mL" in fname[0] else False
    if has_ml:
        fields_u = fields_ml
    else:
        fields_u = fields

    mdict = dict(zip(fields_u,fname[0].split('_')))
    try:
        mdict['plate_size'] = int(mdict['plate_size'])
        mdict['timepoint'] = float(mdict['timepoint'].rstrip('h'))
        mdict['fbs'] = float(mdict['fbs'].lstrip('FBS')) / 10.0
        mdict['insert'] = mdict['insert_passive_dosing'][0] == 'y'
        mdict['passive_dosing'] = mdict['insert_passive_dosing'][1] == 'y'
        mdict['id_string'] = fname[0]
        del mdict['insert_passive_dosing']
        if has_ml:
            mdict['volume'] = float(mdict['volume'].rstrip("mL"))
    except:
        print('Error parsing filename string')
        raise
    return mdict
    



def read_dr(fname,verbose=False):
    if verbose:
        print(fname)
    metadata = parse_file_string(fname)
    rdf = pd.read_excel(fname)
    metadata['replicates'] = sum(rdf.sum() > 0) -1
    new_names = ['concentration'] + [str(x) for x in range(metadata['replicates'])]
    rdf = rdf.rename(columns=dict(zip(list(rdf.columns),new_names)))
    rdfLong = rdf.melt(id_vars=['concentration'],value_name='effect',var_name='replicate')
    
    metadata['raw_data'] = rdfLong.dropna()
    metadata['rawfile_hash'] = hashlib.sha1(open(fname, 'rb').read()).hexdigest()
    metadata['filename'] = fname
    return metadata

def read_estimated(fname):
    df = pd.read_csv(fname)
    df['params'] = df['params'].map(lambda x: x.replace('.','_'))
    return dict(df.values.tolist())
    