# coding=utf-8
from __future__ import unicode_literals
from unittest import TestCase
from ming import create_datastore, Session
from ming.odm import ThreadLocalODMSession


class RootTest(TestCase):
    def setUp(self):
        bind = create_datastore('mongodb://localhost:27017/test_tgext_ecommerce')
        session = Session(bind)
        self.test_session = ThreadLocalODMSession(session)

    def tearDown(self):
        from tgext.ecommerce.lib.shop import models
        self.test_session.remove(models.Product)
        self.test_session.remove(models.Category)
        self.test_session.remove(models.Cart)
        self.test_session = None