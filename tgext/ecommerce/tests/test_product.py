# coding=utf-8
from __future__ import unicode_literals
import datetime
from time import sleep
from tgext.ecommerce.tests import RootTest


class TestProduct(RootTest):
    @classmethod
    def setUpClass(cls):
        from tgext.ecommerce.lib import shop

        cls.old_i_ = shop.i_
        shop.i_ = lambda name: {'it': name}

    @classmethod
    def tearDownClass(cls):
        from tgext.ecommerce.lib import shop

        shop.i_ = cls.old_i_

    def setUp(self):
        super(TestProduct, self).setUp()
        from tgext.ecommerce import model

        self.old_session = model.DBSession
        model.DBSession = self.test_session

    def _create_product(self, shop, sku):
        cat = shop.create_category('ham')
        return shop.create_product(type='product',
                                   sku=sku,
                                   name='test product',
                                   category_id=cat._id,
                                   description='Lorem ipsum dolor sit amet, consectetur adipisicing elit',
                                   price=50,
                                   vat=0.22,
                                   qty=20,
                                   initial_quantity=20,
                                   variety='test variety',
                                   active=True,
                                   valid_from=datetime.datetime.utcnow(),
                                   valid_to=datetime.datetime.utcnow())

    def test_create_product(self):
        from tgext.ecommerce.lib.shop import ShopManager, models

        sm = ShopManager()
        self._create_product(sm, '12345')
        r = models.Product.query.find({'configurations.sku': '12345'}).first()
        assert r is not None, r

    def test_add_to_cart(self):
        from tgext.ecommerce.lib.shop import ShopManager, models

        sm = ShopManager()
        pr = self._create_product(sm, '12345')
        self.assertTrue(sm.buy_product(pr, 0, 2, 'egg'))
        models.DBSession.clear()
        pr = sm.get_product('12345')
        assert pr.configurations[0]['qty'] == 18, pr.configurations[0]['qty']

    def test_cant_buy(self):
        from tgext.ecommerce.lib.shop import ShopManager, models

        sm = ShopManager()
        pr = self._create_product(sm, '12345')
        self.assertFalse(sm.buy_product(pr, 0, 22, 'egg'))
        models.DBSession.clear()
        pr = sm.get_product('12345')
        assert pr.configurations[0]['qty'] == 20, pr.configurations[0]['qty']

    def test_cleanup_cart(self):
        from tgext.ecommerce.lib.shop import ShopManager, models
        from tgext.ecommerce.lib.async_jobs import clean_expired_carts

        #expire cart immediately
        models.CartTtlExt._cart_ttl = 0

        sm = ShopManager()
        pr = self._create_product(sm, '12345')
        sm.buy_product(pr, 0, 2, 'egg')
        models.DBSession.flush_all()
        models.DBSession.close_all()

        clean_expired_carts()
        pr = sm.get_product('12345')
        assert pr.configurations[0]['qty'] == 20, pr.configurations[0]['qty']





