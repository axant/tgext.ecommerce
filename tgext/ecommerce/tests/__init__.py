# coding=utf-8
from __future__ import unicode_literals
from unittest import TestCase
from ming import create_datastore, Session
from ming.odm import ThreadLocalODMSession
from tgext.ecommerce.model import init_model, DBSession


class RootTest(TestCase):
    def setUp(self):
        bind = create_datastore('mongodb://localhost:27017/test_tgext_ecommerce')
        session = Session(bind)
        init_model(ThreadLocalODMSession(session))

    def tearDown(self):
        from tgext.ecommerce.model import models
        DBSession.remove(models.Product)
        DBSession.remove(models.Category)
        DBSession.remove(models.Cart)