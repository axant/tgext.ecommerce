from tg import flash
from tgextecommerce.lib.exceptions import AlreadyExistingSlugException
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
    def create_product(self, type, sku, name, description='', price=1.0,
                       vat=0.0, qty=0, initial_quantity=0,
                       variety=None, active=True, valid_from=None, valid_to=None,
                       configuration_details=None, **details):
        if variety is None:
            variety = name

        if configuration_details is None:
            configuration_details = {}

        slug = slugify(name, type)
        if models.Product.query.find({'slug': slug}).first():
            raise AlreadyExistingSlugException('Already exist a Product with slug: %s' % slug)

        product = models.Product(type=type,
                                 name=name,
                                 description=description,
                                 slug=slug,
                                 details=details,
                                 active=active,
                                 valid_from=valid_from,
                                 valid_to=valid_to,
                                 configurations=[{'sku': sku,
                                                  'variety': variety,
                                                  'price': price,
                                                  'vat': vat,
                                                  'qty': qty,
                                                  'initial_quantity': initial_quantity,
                                                  'details': configuration_details}])

    def get_product(self, sku=None, _id=None, slug=None):
        if _id is not None:
            return models.Product.query.get(_id=_id)
        elif sku is not None:
            return models.Product.query.find({'configurations.sku': sku}).first()
        elif slug is not None:
            return models.Product.query.find({'slug': slug}).first()
        else:
            return None

    def get_products(self, type, query=None, fields=[]):
        if query is None:
            query = {}
        query['type'] = type
        if fields:
            return models.Product.query.find(query, fields=fields)
        return models.Product.query.find(query).all()

    def create_product_configuration(self, slug, sku, price=1.0, vat=0.0, qty=0, initial_quantity=0,
                                     variety=None, **configuration_details):

        product = models.Product.query.find({'slug': slug}).first()
        product.configurations.append({'sku': sku,
                                       'variety': variety,
                                       'price': price,
                                       'vat': vat,
                                       'qty': qty,
                                       'initial_quantity': initial_quantity,
                                       'details': configuration_details})
