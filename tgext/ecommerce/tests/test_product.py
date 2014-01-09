# coding=utf-8
from __future__ import unicode_literals
import datetime
from tgext.ecommerce.tests import RootTest


class TestProduct(RootTest):

    def setUp(self):
        super(TestProduct, self).setUp()
        from tgext.ecommerce import model
        self.old_session = model.DBSession
        model.DBSession = self.test_session

    def test_create_product(self):
        from tgext.ecommerce.lib.shop import ShopManager, models
        sm = ShopManager()
        sm.create_product(type='product',
                          sku='12345',
                          name='test product',
                          description='Lorem ipsum dolor sit amet, consectetur adipisicing elit',
                          price=50,
                          vat=0.22,
                          qty=20,
                          initial_quantity=20,
                          variety='test variety',
                          active=True,
                          valid_from=datetime.datetime.utcnow(),
                          valid_to=datetime.datetime.utcnow(),
                          )
        r = models.Product.query.find({'configurations.sku': '12345'}).first()
        assert r is not None, r




