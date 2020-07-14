# -*- coding: utf-8 -*-
"""
Created on Tue May 12 21:17:23 2020

@author: Alex
"""
import re


def get_float_prec(x, n=0):
    """
    Get the number of positions after decimal for printing floating points.

    Parameters
    ----------
    x : float
        number to be formatted
    n : int, optional
        Number of positions to display after first nonzero position. The default is 0.

    Returns
    -------
    int
        the number of positions after decimal point for display
    """
    if x <= 0:
        return -1
    if x < 1:
        return get_float_prec(x * 10, n + 1)
    else:
        return n


def chemical_title(name):
    """
    Format chemical names such that the first letter in a name is uppercase 
    and all other letters are lowercase

    Parameters
    ----------
    name : string
        Unformatted chemical name

    Returns
    -------
    string
        formatted chemical name

    """
    s = name.lower()
    m = re.search("[a-zA-Z]", s)
    idx = m.start(0)
    sl = list(s)
    sl[idx] = sl[idx].upper()
    return "".join(sl)


def format_helper(x, precision):
    """
    Format a float in exponential notation if it is larger thant 1E5 or smaller
    than 1E-5

    Parameters
    ----------
    x : TYPE
        DESCRIPTION.
    precision : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    if x > 1E5 or x < 1E-5:
        return '{:.2e}'.format(x)
    else:
        return "{:.{}f}".format(x, precision + 1)
