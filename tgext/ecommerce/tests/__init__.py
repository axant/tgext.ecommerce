# coding=utf-8
from __future__ import unicode_literals
from unittest import TestCase
from ming import create_datastore, Session
from ming.odm import ThreadLocalODMSession

class RootTest(TestCase):

    def setUp(self):
        bind = create_datastore('mim://')
        session = Session(bind)
        self.test_session = ThreadLocalODMSession(session)

    def tearDown(self):
        self.test_session = None