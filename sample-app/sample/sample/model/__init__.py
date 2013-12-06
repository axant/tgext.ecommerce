# -*- coding: utf-8 -*-
"""The application's model objects"""

import ming.orm
from session import mainsession, DBSession

def init_model(engine):
    """Call me before using any of the tables or classes in the model."""
    mainsession.bind = engine
    ming.orm.Mapper.compile_all()

    for mapper in ming.orm.Mapper.all_mappers():
        mainsession.ensure_indexes(mapper.collection)

# Import your model modules here.
from sample.model.auth import User, Group, Permission
