from tg import app_globals
from formencode import FancyValidator, Invalid
from tw2.core import Validator, ValidationError
from bson import ObjectId


class ProductValidator(FancyValidator):
    def __init__(self, using='_id'):
        super(ProductValidator, self).__init__(not_empty=True)
        self.using = using

    def _convert_to_python(self, value, state):
        kwargs = {self.using: value}
        product = app_globals.shop.product.get(**kwargs)

        if product is None:
            raise Invalid('Product not found', value, state)

        if not product.active:
            raise Invalid('Product not valid', value, state)

        return product


class UniqueSkuValidator(Validator):
    msgs = {'existing_sku':'There is already a product with this SKU',
           'invalid_sku':'SKU is required'}

    def __init__(self, sku, product_id=None, **kw):
        super(UniqueSkuValidator, self).__init__(**kw)
        self.product_id = product_id
        self.sku = sku

    def _validate_python(self, values, state=None):
        if not isinstance(values.get(self.sku), basestring):
            raise ValidationError('invalid_sku', self)
        product = app_globals.shop.product.get(sku=values.get(self.sku))
        if product:
            if ObjectId(values.get(self.product_id))!=product._id:
                raise ValidationError('existing_sku', self)


