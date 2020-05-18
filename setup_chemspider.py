# -*- coding: utf-8 -*-
"""
Created on Sun Apr 12 13:44:08 2020

@author: Alex
"""
from chemspipy import ChemSpider
import csv

def setup_chemspi():
    with open("config.txt") as tsvfile:
        tsvreader = csv.reader(tsvfile, delimiter="\t")
        for line in tsvreader:
            if line[0] == 'CHEMSPIDER-API-KEY':        
                cs = ChemSpider(line[1])
    return cs