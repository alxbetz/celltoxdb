#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 30 11:16:29 2020

@author: alx
"""

from wtforms.validators import DataRequired, Optional


class RequiredIfNot(DataRequired):
    """Validator which makes a field not required if another field is set and has a truthy value."""

    field_flags = ('requiredifnot', )

    def __init__(self, message=None, *args, **kwargs):
        super(RequiredIfNot).__init__()
        self.message = message
        self.conditions = kwargs

    # field is requiring that name field in the form is data value in the form
    def __call__(self, form, field):
        for name, data in self.conditions.items():
            other_field = form[name]
            if other_field is None:
                raise Exception('no field named "%s" in form' % name)
            if other_field.data == data and not field.data:
                DataRequired.__call__(self, form, field)
            Optional()(form, field)
