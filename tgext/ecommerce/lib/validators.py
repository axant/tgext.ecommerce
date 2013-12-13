from tg import app_globals
from formencode import FancyValidator, Invalid


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