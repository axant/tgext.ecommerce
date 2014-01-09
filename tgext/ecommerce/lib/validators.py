from tg import app_globals
from formencode import FancyValidator, Invalid
from tw2.core import Validator, ValidationError


class ProductValidator(FancyValidator):
    def __init__(self, using='_id'):
        super(ProductValidator, self).__init__(not_empty=True)
        self.using = using

    def _to_python(self, value, state):
        kwargs = {self.using: value}
        product = app_globals.shop.get_product(**kwargs)

        if product is None:
            raise Invalid('Product not found', value, state)

        if not product.active:
            raise Invalid('Product not valid', value, state)

        return product


class UniqueSkuValidator(Validator):
    msg = 'There is already a product with this SKU'

    def _validate_python(self, value, state=None):
        if app_globals.shop.get_product(sku=value):
            raise ValidationError(self.msg, self)
