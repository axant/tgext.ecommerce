from tgextecommerce.lib.utils import slugify


class Models(object):
    def __init__(self):
        self._models = None

    @property
    def models(self):
        if self._models is None:
            from tgextecommerce.model import models
            self._models = models
        return self._models

    def __getattr__(self, item):
        return getattr(self.models, item)

models = Models()


class ShopManager(object):
    def create_product(self, type, sku, name, description='',
                       price=1.0, vat=0.0, qty=0, initial_quantity=0,
                       variety=None, active=True, **details):
        if variety is None:
            variety = name

        product = models.Product(type=type,
                                 name=name,
                                 description=description,
                                 slug=slugify(name),
                                 details=details,
                                 active=active,
                                 configurations=[{'sku': sku,
                                                  'variety': variety,
                                                  'price': price,
                                                  'vat': vat,
                                                  'qty': qty,
                                                  'initial_quantity': initial_quantity}])

    def get_product(self, sku=None, _id=None):
        if _id is not None:
            return models.Product.query.get(_id=_id)
        else:
            return models.Product.query.find({'configurations.sku': sku}).first()