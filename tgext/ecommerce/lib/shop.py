
from tgext.ecommerce.lib.cart import CartManager
from tgext.ecommerce.lib.category import CategoryManager
from tgext.ecommerce.lib.order import OrderManager
from tgext.ecommerce.lib.payments import paypal, null_payment
from tgext.ecommerce.lib.product import ProductManager


class ShopManager(object):
    cart = CartManager()
    product = ProductManager()
    category = CategoryManager()
    order = OrderManager()

    def pay(self, cart, redirection_url, cancel_url, paymentService=paypal):
        return paymentService.pay(cart, redirection_url, cancel_url)

    def confirm(self, cart, redirection, data, paymentService=paypal):
        return paymentService.confirm(cart, redirection, data)

    #@param data has to be composed by the first name, last name and redirect url in case of 3D Secure
    def execute(self, cart, data, paymentService=paypal):
        return paymentService.execute(cart, data)

    def secure_3ds_handler(self, cart, data, paymentService=null_payment):
        return paymentService.secure_3d(cart, data)


