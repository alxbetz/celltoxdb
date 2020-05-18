# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 10:11:31 2020

@author: Alex
"""

fields = [
    'cell_line',
    'experimenter',
    'plate_size',
    'timepoint',
    'endpoint',
    'medium',
    'FBS',
    'insert_passive_dosing',
    'dosing', #direct or indirect
    'concentration_measurement',
    'solvent',
    'cas_number'
    ]


def parse_file_string(s):
    fname = s.split('.')
    mdict = dict(zip(fields,fname[0].split('_')))
    try:
        mdict['plate_size'] = int(mdict['plate_size'])
        mdict['timepoint'] = float(mdict['timepoint'].rstrip('h'))
        mdict['FBS'] = float(mdict['FBS'].lstrip('FBS')) / 10.0
        mdict['insert'] = mdict['insert_passive_dosing'][0] == 'y'
        mdict['passive_dosing'] = mdict['insert_passive_dosing'][1] == 'y'
        del mdict['insert_passive_dosing']
    except:
        print('Error converting file ')
    return mdict
    


import os


s1 = "GIL_fab_24_0048h_CF_m1_FBS00_nn_in_no_D_84268-36-0.xlsx"
parse_file_string(s1)

files = list(filter(lambda x: not x.startswith('.~lock'),os.listdir('..\\rawdata')))
res = [parse_file_string(s) for s in files]