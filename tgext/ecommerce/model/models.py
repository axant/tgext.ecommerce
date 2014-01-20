from datetime import datetime, timedelta
from ming.odm.property import ORMProperty
from ming.odm import FieldProperty, ForeignIdProperty, RelationProperty, MapperExtension
from ming.odm.declarative import MappedClass
from ming import schema as s
import tg
from tg.caching import cached_property
from tgext.ecommerce.lib.utils import short_lang
from tgext.ecommerce.model import DBSession


class Category(MappedClass):
    class __mongometa__:
        session = DBSession
        name = 'categories'

    _id = FieldProperty(s.ObjectId)
    name = FieldProperty(s.Anything, required=True)

    @property
    def i18n_name(self):
        return self.name.get(tg.translator.preferred_language, self.name.get(tg.config.lang))


class Product(MappedClass):
    class __mongometa__:
        session = DBSession
        name = 'products'
        unique_indexes = [('slug',),
                          ('configurations.sku',)
                          ]
        indexes = [('type', 'active', ('valid_to', -1)),
                   ('type', 'category_id', 'active')]

    _id = FieldProperty(s.ObjectId)
    name = FieldProperty(s.Anything, required=True)
    type = FieldProperty(s.String, required=True)
    category_id = ForeignIdProperty(Category)
    category = RelationProperty(Category)
    description = FieldProperty(s.Anything, if_missing='')
    slug = FieldProperty(s.String, required=True)
    details = FieldProperty(s.Anything, if_missing={})
    active = FieldProperty(s.Bool, if_missing=True)
    valid_from = FieldProperty(s.DateTime)
    valid_to = FieldProperty(s.DateTime)
    configurations = FieldProperty([{
        'variety': s.Anything(required=True),
        'qty': s.Int(required=True),
        'initial_quantity': s.Int(required=True),
        'sku': s.String(required=True),
        'price': s.Float(required=True),
        'vat': s.Float(required=True),
        'details': s.Anything(if_missing={}),
    }])

    @cached_property
    def min_price(self):
        return '%.2f' % min(map(lambda conf: conf['price'] * (1+conf['vat']), self.configurations))

    @property
    def thumbnail(self):
        return tg.url(self.details['product_photos'][0]['url']) if self.details['product_photos'] else '//placehold.it/300x300'

    @property
    def i18n_name(self):
        return self.name.get(tg.translator.preferred_language, self.name.get(tg.config.lang))

    @property
    def i18n_description(self):
        return self.description.get(tg.translator.preferred_language, self.description.get(tg.config.lang))

    def i18n_configuration_variety(self, configuration):
        return configuration.variety.get(tg.translator.preferred_language, configuration.variety.get(tg.config.lang))


class CartTtlExt(MapperExtension):

    _cart_ttl = None

    @classmethod
    def cart_expiration(cls):
        if cls._cart_ttl is None:
            cls._cart_ttl = int(tg.config.get('cart.ttl', 30*60))
        return datetime.utcnow() + timedelta(seconds=cls._cart_ttl)

    def before_update(self, instance, state, sess):
        instance.expires_at = self.cart_expiration()


class Cart(MappedClass):
    class __mongometa__:
        session = DBSession
        name = 'carts'
        unique_indexes = [('user_id', )]
        indexes = [('expires_at', )]
        extensions = [CartTtlExt]

    _id = FieldProperty(s.ObjectId)
    user_id = FieldProperty(s.String, required=True)
    items = FieldProperty(s.Anything, if_missing={})
    expires_at = FieldProperty(s.DateTime, if_missing=CartTtlExt.cart_expiration)

    @classmethod
    def expired_carts(cls):
        return cls.query.find({'expires_at': {'$lte': datetime.utcnow()}})
