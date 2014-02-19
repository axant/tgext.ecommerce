# coding=utf-8
from __future__ import unicode_literals
from tgext.ecommerce.lib.product import ProductManager
from tgext.ecommerce.model import models


class CartManager(object):

    @classmethod
    def create_or_get(cls, user_id):  #create_or_get_cart
        cart = cls.get(user_id)
        if cart is None:
            cart = models.Cart(user_id=user_id)
            models.DBSession.flush()
        return cart

    @classmethod
    def get(cls, user_id):  #get_cart
        return models.Cart.query.find({'user_id': user_id}).first()

    @classmethod
    def update_item_qty(cls, cart, sku, qty): #update_cart_item_qty
        product_in_cart = cart.items.get(sku, {})
        already_bought = product_in_cart.get('qty', 0)
        delta_qty = qty - already_bought
        if delta_qty == 0:
            return cart
        product = ProductManager.get(sku=sku)
        ProductManager.buy(cart, product, ProductManager._config_idx(product, sku), delta_qty)
        return cart

    @classmethod
    def delete_item(cls, cart, sku):  #delete_from_cart
        return cls.update_item_qty(cart, sku, 0)
