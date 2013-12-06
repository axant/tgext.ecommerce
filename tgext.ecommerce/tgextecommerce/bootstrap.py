# -*- coding: utf-8 -*-
"""Setup the tgextecommerce application"""

from tgextecommerce import model
from tgext.pluggable import app_model

def bootstrap(command, conf, vars):
    print 'Bootstrapping tgextecommerce...'

    s1 = model.Sample()
    s1.name = 'Test Sample'
    s1.user = model.DBSession.query(app_model.User).first()

    model.DBSession.add(s1)
    model.DBSession.flush()