from tg import app_globals
from formencode import FancyValidator, Invalid
from tw2.core import Validator, ValidationError
from bson import ObjectId


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

    def __init__(self, sku, product_id=None, **kw):
        super(UniqueSkuValidator, self).__init__(**kw)
        self.product_id = product_id
        self.sku = sku

    def _validate_python(self, values, state=None):
        product = app_globals.shop.get_product(sku=values.get(self.sku))

        if ObjectId(values.get(self.product_id))!=product._id:
            raise ValidationError(self.msg, self)


