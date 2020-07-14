#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 13:05:36 2020

@author: alx
"""

import os
import glob
import pandas as pd

exceeds_names = ["estimated.csv" ".png"]
ec_names = exceeds_names + ['plotdata.csv', 'RDS']

val_names = {
    "plot": "Plot size > 0",
    "rdata": "R data size > 0",
    "plotdata": "Plot data has the right shape",
    "EC": "EC50 value is not zero",
    'slope': "Slope is non zero and negative",
    "confint": "Confidence intervals are not 0 or inf",
    'exceeds_direction': "Exceed direction is not null",
    'exceeds_value': "Exceed value is not null or nan"
}


def validate_drc(folder):
    """
    tests whether the output of the dose response curve calculation is
    well formed

    Parameters
    ----------
    folder : string
        output folder of R dose response curve calculation

    Returns
    -------
    val : dict
        binary result for each test

    """
    val = {}
    try:
        estimated_fname = glob.glob(os.path.join(folder, "*estimated.csv"))[0]
        rdata_fname = glob.glob(os.path.join(folder, "*RDS"))[0]
        plotdata_fname = glob.glob(os.path.join(folder, "*plotdata.csv"))[0]
        plot_fname = glob.glob(os.path.join(folder, "*png"))[0]

        estimated = dict(pd.read_csv(estimated_fname).values)
        print(estimated)
        plotdata = pd.read_csv(plotdata_fname)
        rdata_stat = os.stat(rdata_fname)
        plot_stat = os.stat(plot_fname)

        #check that the plot file is not empty
        if plot_stat.st_size > 0:
            val['plot'] = True
        #check that rdata file is not empty
        if rdata_stat.st_size > 0:
            val['rdata'] = True
        #check if plot data file has the right size
        if plotdata.shape[0] > 999 and plotdata.shape[1] == 4:
            val['plotdata'] = True
        if estimated['ec50'] != 0 and estimated['ec10'] != 0:
            val['EC'] = True
        if estimated['slope'] < -1E-10:
            val['slope'] = True
        if estimated['ec50.ci.lower'] != 0 and \
        estimated['ec50.ci.lower'] != float('-inf') and \
        estimated['ec50.ci.upper'] != 0 and \
        estimated['ec50.ci.upper'] != float('inf'):
            val['confint'] = True

    except:
        val['plot'] = False
        val['rdata'] = False
        val['plotdata'] = False
        val['EC'] = False
        val['slope'] = False
        val['confint'] = False

    return val


def validate_exceeds(folder):
    """ validate the results when no EC50 can be calculated """
    val = {}
    try:
        estimated_fname = glob.glob(os.path.join(folder, "*estimated.csv"))[0]
        plot_fname = glob.glob(os.path.join(folder, "*png"))[0]
        estimated = dict(pd.read_csv(estimated_fname))
        plot_stat = os.stat(plot_fname)

        #check that the plot file is not empty
        if plot_stat.st_size > 0:
            val['plot'] = True

        #check that exceeds direction is nonempty and
        if estimated['exceeds_value'] != 0:
            val['exceeds_value'] = True
        if type(estimated['exceeds_direction']) == str and \
            len(estimated['exceeds_direction']) > 0 and \
                not pd.isna(estimated['exceeds_direction']):
            val['exceeds_direction'] = True
    except:
        val['exceeds_value'] = False
        val['exceeds_direction'] = False

    return val


def validate_ec_calculation(folder):
    """ wrapper function that determines which of the tests to apply"""
    nfiles = len(os.listdir(folder))
    if nfiles > 3:
        val = validate_drc(folder)
    else:
        val = validate_exceeds(folder)
    valr = {val_names[k]: v for k, v in val.items()}
    return valr
