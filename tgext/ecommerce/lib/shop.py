import sys
import datetime
import tg
from tgext.ecommerce.lib.cart import CartManager
from tgext.ecommerce.lib.category import CategoryManager
from tgext.ecommerce.lib.exceptions import CategoryAssignedToProductException
from tgext.ecommerce.lib.order import OrderManager
from tgext.ecommerce.lib.payments import paypal
from tgext.ecommerce.lib.product import ProductManager
from tgext.ecommerce.lib.utils import slugify, internationalise as i_
from tgext.ecommerce.model import models
from bson import ObjectId
from collections import Counter



class ShopManager(object):
    cart = CartManager()
    product = ProductManager()
    category = CategoryManager()
    order = OrderManager()

    def pay(self, cart, redirection_url, cancel_url, shipping_charges=0):
        return paypal.pay(cart, redirection_url, cancel_url, shipping_charges)

    def confirm(self, cart, redirection, data):
        return paypal.confirm(cart, redirection, data)

    def execute(self, cart, data):
        return paypal.execute(cart, data)
