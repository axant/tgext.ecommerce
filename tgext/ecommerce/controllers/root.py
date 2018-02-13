# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import TGController, expose, flash, require, url, lurl, request, redirect, validate, hooks, config, abort
from tg.i18n import ugettext as _, lazy_ugettext as l_

from tgext.ecommerce import model
from tgext.ecommerce.controllers.manage import ManageController
from tgext.ecommerce.controllers.sagePayment import SagePaymentController
import json
import requests
from bson import ObjectId

class RootController(TGController):
    manage = ManageController()
    sage = SagePaymentController()




