# coding=utf-8
from __future__ import unicode_literals
import datetime
from time import sleep
from tgext.ecommerce.tests import RootTest


class TestShop(RootTest):
    @classmethod
    def setUpClass(cls):
        from tgext.ecommerce.lib import product
        from tgext.ecommerce.lib import category

        cls.old_i_ = product.i_
        product.i_ = lambda name: {'it': name}
        category.i_ = lambda name: {'it': name}

    @classmethod
    def tearDownClass(cls):
        from tgext.ecommerce.lib import product
        from tgext.ecommerce.lib import category

        product.i_ = cls.old_i_
        category.i_ = cls.old_i_

    def setUp(self):
        super(TestShop, self).setUp()

    def _create_product(self, shop, sku, published=False):
        cat = shop.category.create('ham')
        return shop.product.create(type='product',
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
                                   valid_to=datetime.datetime.utcnow(),
                                   published=published)

    def test_create_product(self):
        from tgext.ecommerce.lib.shop import ShopManager
        from tgext.ecommerce.model import models


        sm = ShopManager()
        self._create_product(sm, '12345')
        r = models.Product.query.find({'configurations.sku': '12345'}).first()
        assert r is not None, r

    def test_get_product_by_sku(self):
        from tgext.ecommerce.lib.shop import ShopManager
        from tgext.ecommerce.model import models

        sm = ShopManager()
        self._create_product(sm, '12345')
        models.DBSession.flush_all()
        models.DBSession.close_all()

        product = sm.product.get(sku='12345')
        self.assertEqual(product.configurations[0]['sku'], '12345')

    def test_add_to_cart(self):
        from tgext.ecommerce.lib.shop import ShopManager
        from tgext.ecommerce.model import models

        sm = ShopManager()
        pr = self._create_product(sm, '12345')
        self.assertTrue(sm.product.buy(sm.cart.create_or_get('egg'), pr, 0, 2))
        models.DBSession.clear()
        pr = sm.product.get('12345')
        assert pr.configurations[0]['qty'] == 18, pr.configurations[0]['qty']

    def test_not_enough_products(self):
        from tgext.ecommerce.lib.shop import ShopManager
        from tgext.ecommerce.model import models

        sm = ShopManager()
        pr = self._create_product(sm, '12345')
        self.assertFalse(sm.product.buy(sm.cart.create_or_get('egg'), pr, 0, 22))
        models.DBSession.clear()
        pr = sm.product.get('12345')
        assert pr.configurations[0]['qty'] == 20, pr.configurations[0]['qty']

    def test_not_enough_product_after(self):
        from tgext.ecommerce.lib.shop import ShopManager
        from tgext.ecommerce.model import models

        sm = ShopManager()
        pr = self._create_product(sm, '12345')
        cart = sm.cart.create_or_get('egg')
        self.assertTrue(sm.product.buy(cart, pr, 0, 12))
        self.assertFalse(sm.product.buy(cart, pr, 0, 14))
        models.DBSession.flush_all()
        models.DBSession.close_all()

        pr = sm.product.get('12345')
        self.assertEqual(pr.configurations[0]['qty'], 8)

    def test_cleanup_cart(self):
        from tgext.ecommerce.lib.shop import ShopManager
        from tgext.ecommerce.lib.async_jobs import clean_expired_carts
        from tgext.ecommerce.model import models

        #expire cart immediately
        models.CartTtlExt._cart_ttl = 0

        sm = ShopManager()
        pr = self._create_product(sm, '12345')
        sm.product.buy(sm.cart.create_or_get('egg'), pr, 0, 2)
        models.DBSession.flush_all()
        models.DBSession.close_all()

        clean_expired_carts()
        pr = sm.product.get('12345')

        self.assertEqual(pr.configurations[0]['qty'], 20)

        cart = sm.cart.get('egg')
        self.assertIsNone(cart)

    def test_delete_item_from_cart(self):
        from tgext.ecommerce.lib.shop import ShopManager
        from tgext.ecommerce.model import models

        sm = ShopManager()
        pr = self._create_product(sm, '12345')
        sm.product.buy(sm.cart.create_or_get('egg'), pr, 0, 2)
        models.DBSession.flush_all()
        models.DBSession.close_all()

        cart = sm.cart.get('egg')
        self.assertIn('12345', cart.items)
        sm.cart.delete_item(cart, '12345')
        models.DBSession.flush_all()
        models.DBSession.close_all()

        cart = sm.cart.get('egg')
        self.assertNotIn('12345', cart.items)

    def test_update_cart_item_qty(self):
        from tgext.ecommerce.lib.shop import ShopManager
        from tgext.ecommerce.model import models

        sm = ShopManager()
        pr = self._create_product(sm, '12345')
        sm.product.buy(sm.cart.create_or_get('egg'), pr, 0, 2)
        models.DBSession.flush_all()
        models.DBSession.close_all()

        cart = sm.cart.get('egg')
        sm.cart.update_item_qty(cart, '12345', 4)
        models.DBSession.flush_all()
        models.DBSession.close_all()

        pr = sm.product.get('12345')
        self.assertEqual(pr.configurations[0]['qty'], 16)

    def test_update_cart_item_qty_noop(self):
        from tgext.ecommerce.lib.shop import ShopManager
        from tgext.ecommerce.model import models

        sm = ShopManager()
        pr = self._create_product(sm, '12345')
        sm.product.buy(sm.cart.create_or_get('egg'), pr, 0, 2)
        models.DBSession.flush_all()
        models.DBSession.close_all()

        cart = sm.cart.get('egg')
        sm.cart.update_item_qty(cart, '12345', 2)
        models.DBSession.flush_all()
        models.DBSession.close_all()

        pr = sm.product.get('12345')
        self.assertEqual(pr.configurations[0]['qty'], 18)

    def test_search_product(self):
        from tgext.ecommerce.lib.shop import ShopManager
        from tgext.ecommerce.model import models

        sm = ShopManager()
        self._create_product(sm, '12345', published=True)
        models.DBSession.flush_all()
        models.DBSession.close_all()

        products = sm.product.search('product', language='it').count()
        self.assertEqual(products, 1)
        models.DBSession.close_all()

        products = sm.product.search('lorem', language='it').count()
        self.assertEqual(products, 1)
