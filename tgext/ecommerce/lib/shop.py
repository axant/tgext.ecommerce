import tg
from tgext.ecommerce.lib.exceptions import AlreadyExistingSlugException, AlreadyExistingSkuException, \
    CategoryAssignedToProductException
from tgext.ecommerce.lib.utils import slugify, internationalise as i_
from bson import ObjectId
from ming.odm import mapper


class Models(object):
    def __init__(self):
        self._models = None

    @property
    def models(self):
        if self._models is None:
            from tgext.ecommerce.model import models

            self._models = models
        return self._models

    def __getattr__(self, item):
        return getattr(self.models, item)


models = Models()


class ShopManager(object):
    def create_product(self, type, sku, name, category_id=None, description='', price=1.0,
                       vat=0.0, qty=0, initial_quantity=0,
                       variety=None, active=True, valid_from=None, valid_to=None,
                       configuration_details=None, **details):
        if variety is None:
            variety = name

        if configuration_details is None:
            configuration_details = {}

        slug = slugify(name, type, models)
        if models.Product.query.find({'slug': slug}).first():
            raise AlreadyExistingSlugException('Already exist a Product with slug: %s' % slug)

        if models.Product.query.find({'configurations.sku': sku}).first():
            raise AlreadyExistingSkuException('Already exist a Configuration with sku: %s' % sku)

        models.Product(type=type,
                       name=i_(name),
                       category_id=ObjectId(category_id) if category_id else None,
                       description=i_(description),
                       slug=slug,
                       details=details,
                       active=active,
                       valid_from=valid_from,
                       valid_to=valid_to,
                       configurations=[{'sku': sku,
                                        'variety': i_(variety),
                                        'price': price,
                                        'vat': vat,
                                        'qty': qty,
                                        'initial_quantity': initial_quantity,
                                        'details': configuration_details}])
        models.DBSession.flush()

    def create_product_configuration(self, product, sku, price=1.0, vat=0.0,
                                     qty=0, initial_quantity=0, variety=None,
                                     **configuration_details):

        if models.Product.query.find({'configurations.sku': sku}).first():
            raise AlreadyExistingSkuException('Already exist a Configuration with sku: %s' % sku)

        product.configurations.append({'sku': sku,
                                       'variety': i_(variety),
                                       'price': price,
                                       'vat': vat,
                                       'qty': qty,
                                       'initial_quantity': initial_quantity,
                                       'details': configuration_details})

    def get_product(self, sku=None, _id=None, slug=None):
        if _id is not None:
            return models.Product.query.get(_id=ObjectId(_id))
        elif sku is not None:
            return models.Product.query.find({'configurations.sku': sku}).first()
        elif slug is not None:
            return models.Product.query.find({'slug': slug}).first()
        else:
            return None

    def get_products(self, type, query=None, fields=None, limit=None, skip=None):
        filter = {'type': type}
        filter.update(query or {})
        q_kwargs = {}
        if fields:
            q_kwargs['fields'] = fields
        q = models.Product.query.find(filter, **q_kwargs)
        if limit is not None:
            q = q.limit(limit)
        if skip is not None:
            q = q.skip(limit)
        return q

    def delete_product(self, product):
        product.active = False

    def buy_product(self, product, configuration_index, amount):
        quantity_field = 'configurations.%s.qty' % configuration_index
        result = models.DBSession.impl.update_partial(mapper(models.Product).collection,
                                                      {'_id': product._id,
                                                       quantity_field: {'$gte': amount}},
                                                      {'$inc': {quantity_field: -amount}})
        bought = result.get('updatedExisting', False)

        return bought

    def create_category(self, name):
        models.Category(name=i_(name))
        models.DBSession.flush()

    def get_categories(self):
        return models.Category.query.find()

    def get_category(self, _id=None, name=None):
        if _id:
            return models.Category.query.get(_id=ObjectId(_id))
        name_lang = 'name.%s' % tg.config.lang
        return models.Category.query.find({name_lang: name}).first()

    def delete_category(self, _id):
        if models.Product.query.find({'category_id': ObjectId(_id), 'active': True}).first():
            raise CategoryAssignedToProductException('The Category is assigned to an active Product')

        models.Category.query.get(_id=ObjectId(_id)).delete()
        models.Product.query.update({'category_id': ObjectId(_id), 'active': False},
                                    {'$set': {'category_id': None}})
