# -*- coding: utf-8 -*-
from tgext.pluggable import PluggableSession
import ming

DBSession = PluggableSession()

def init_model(app_session):
    DBSession.configure(app_session)