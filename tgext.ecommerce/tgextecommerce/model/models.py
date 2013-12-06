from ming.odm import FieldProperty
from ming.odm.declarative import MappedClass
from ming import schema as s
from tgextecommerce.model import DBSession


class Product(MappedClass):
    class __mongometa__:
        session = DBSession
        name = 'products'
        unique_indexes = [('slug',),
                          ('configurations.sku',)]

    _id = FieldProperty(s.ObjectId)
    name = FieldProperty(s.String, required=True)
    type = FieldProperty(s.String, required=True)
    description = FieldProperty(s.String, if_missing='')
    slug = FieldProperty(s.String, required=True)
    details = FieldProperty(s.Anything, if_missing={})
    active = FieldProperty(s.Bool, if_missing=True)
    configurations = FieldProperty([{
        'variety': s.String(required=True),
        'qty': s.Int(required=True),
        'initial_quantity': s.Int(required=True),
        'sku': s.String(required=True),
        'price': s.Float(reqired=True),
        'vat': s.Float(required=True),
    }])


