# -*- coding: utf-8 -*-
"""
Created on Tue May 12 21:17:23 2020

@author: Alex
"""
import re

def get_float_prec(x,n=0):
    print(type(x))
    if x <= 0:
        return -1
    if x<1:
        return get_float_prec(x*10,n+1)
    else:
        return n
    
def chemical_title(name):
    s = name.lower()
    m = re.search("[a-zA-Z]",s)
    idx = m.start(0)
    sl = list(s)
    sl[idx] = sl[idx].upper()
    return "".join(sl)



