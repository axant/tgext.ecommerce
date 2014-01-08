from ming.odm import FieldProperty, ForeignIdProperty, RelationProperty
from ming.odm.declarative import MappedClass
from ming import schema as s
import tg
from tgext.ecommerce.lib.utils import short_lang
from tgext.ecommerce.model import DBSession


class Product(MappedClass):
    class __mongometa__:
        session = DBSession
        name = 'products'
        unique_indexes = [('slug',),
                          ('configurations.sku',)
                          ]
        indexes = [('type', 'active', ('valid_to', -1))]

    _id = FieldProperty(s.ObjectId)
    name = FieldProperty(s.String, required=True)
    type = FieldProperty(s.String, required=True)
    category_id = ForeignIdProperty('categories')
    category = RelationProperty('categories')
    description = FieldProperty(s.String, if_missing='')
    slug = FieldProperty(s.String, required=True)
    details = FieldProperty(s.Anything, if_missing={})
    active = FieldProperty(s.Bool, if_missing=True)
    valid_from = FieldProperty(s.DateTime)
    valid_to = FieldProperty(s.DateTime)
    configurations = FieldProperty([{
        'variety': s.String(required=True),
        'qty': s.Int(required=True),
        'initial_quantity': s.Int(required=True),
        'sku': s.String(required=True),
        'price': s.Float(required=True),
        'vat': s.Float(required=True),
        'details': s.Anything(if_missing={}),
    }])


class Category(MappedClass):
    class __mongometa__:
        session = DBSession
        name = 'categories'

    _id = FieldProperty(s.ObjectId)
    name = FieldProperty(s.Document, required=True)


    @property
    def i18n_name(self):
        return self.name.get(short_lang(tg.i18n.get_lang()), self.name.get(tg.config.lang))

