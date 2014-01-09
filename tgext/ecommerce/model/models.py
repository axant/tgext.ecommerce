from ming.odm import FieldProperty, ForeignIdProperty, RelationProperty
from ming.odm.declarative import MappedClass
from ming import schema as s
import tg
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
        return self.name.get(short_lang(tg.i18n.get_lang()), self.name.get(tg.config.lang))

class VarietyDict(s.Object):

    @property
    def i18n_variety(self):
        return self.field_items[tg.translator.preferred_language or tg.config.lang]

class Product(MappedClass):
    class __mongometa__:
        session = DBSession
        name = 'products'
        unique_indexes = [('slug',),
                          ('configurations.sku',)
                          ]
        indexes = [('type', 'active', ('valid_to', -1)),
                   ('category_id', 'active')]

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

    @property
    def i18n_name(self):
        return self.name.get(tg.translator.preferred_language, self.name.get(tg.config.lang))

    @property
    def i18n_description(self):
        return self.description.get(tg.translator.preferred_language, self.description.get(tg.config.lang))

    @property
    def i18n_variety(self):
        return self.configurations.variety.get(short_lang(tg.i18n.get_lang()), self.name.get(tg.config.lang))