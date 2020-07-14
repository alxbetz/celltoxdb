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
    'dosing',  #direct or indirect
    'conc_determination',
    'solvent',
    'cas_number'
]

fields_ml = fields[:7] + ["volume"] + fields[7:]


def parse_file_string(s):
    """
    

    Parameters
    ----------
    s : string
        file string containting metadata about exposure

    Returns
    -------
    mdict : dict
        parsed information

    """
    s = ntpath.basename(s)
    fname = os.path.splitext(s)
    has_ml = True if "mL" in fname[0] else False
    if has_ml:
        fields_u = fields_ml
    else:
        fields_u = fields

    mdict = dict(zip(fields_u, fname[0].split('_')))
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


def read_rawdata(fname):
    """
    read dose response raw data

    Parameters
    ----------
    fname : string
        filename

    Raises
    ------
    
        DESCRIPTION.
    IOError
        DESCRIPTION.

    Returns
    -------
    pandas dataframe
        exposure data in long format

    """

    if fname.endswith("csv"):
        rdf = pd.read_csv(fname)
    elif fname.endswith('xls') or fname.endswith('xlsx'):
        rdf = pd.read_excel(fname)
    else:
        raise IOError("Invalid filetype, please use only xls, xlsx or csv")
    rdf = rdf.loc[:, rdf.sum() > 0]
    nrep = len(rdf.columns) - 1
    new_names = ['concentration'] + [str(x) for x in range(nrep)]
    rdf = rdf.rename(columns=dict(zip(list(rdf.columns), new_names)))
    if (rdf.shape[0] == 0):
        raise IOError("File is empty")
    rdfLong = rdf.melt(id_vars=['concentration'],
                       value_name='effect',
                       var_name='replicate')
    return rdfLong.dropna()


def read_dr(fname, verbose=False):
    """
    read dose response curve estimation results

    Parameters
    ----------
    fname : string
        filename
    verbose : boolean, optional
        print filename. The default is False.

    Returns
    -------
    metadata : dict
        metadata.

    """
    
    if verbose:
        print(fname)
    metadata = parse_file_string(fname)
    metadata['errors'] = ''

    try:
        rdfLong = read_rawdata(fname)

        metadata['replicates'] = len(rdfLong.replicate.unique())

        metadata['raw_data'] = rdfLong
        metadata['rawfile_hash'] = hashlib.sha1(open(fname,
                                                     'rb').read()).hexdigest()
    except IOError:
        metadata['errors'] = "File was empty"

    metadata['filename'] = fname
    return metadata


def read_estimated(fname):
    """
    read file containint estimated ec and ntc values

    Parameters
    ----------
    fname : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    df = pd.read_csv(fname)
    df['params'] = df['params'].map(lambda x: x.replace('.', '_'))
    return dict(df.values.tolist())
