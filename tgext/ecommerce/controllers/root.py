# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import TGController
from tg import expose, flash, require, url, lurl, request, redirect, validate
from tg.i18n import ugettext as _, lazy_ugettext as l_

from tgext.ecommerce import model
from tgext.ecommerce.controllers.manage import ManageController
from tgext.ecommerce.model import DBSession


class RootController(TGController):
    manage = ManageController()

    @expose()
    def index(self):
        return 'HELLO'
