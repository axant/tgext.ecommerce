from datetime import datetime, timedelta
from itertools import groupby, imap, chain
from bson import ObjectId
import math
from ming.odm.property import ORMProperty
from ming.odm import FieldProperty, ForeignIdProperty, RelationProperty, MapperExtension
from ming.odm.declarative import MappedClass
from ming import schema as s, DESCENDING, ASCENDING
import tg
from tg import cache
from tg.caching import cached_property
from tg.util import Bunch
from tgext.pluggable import app_model
from tgext.ecommerce.lib.utils import short_lang, preferred_language, apply_vat, with_currency
from tgext.ecommerce.model import DBSession
import operator


class Category(MappedClass):
    class __mongometa__:
        session = DBSession
        name = 'categories'

    _id = FieldProperty(s.ObjectId)
    name = FieldProperty(s.Anything, required=True)
    slug = FieldProperty(s.String)
    parent = FieldProperty(s.ObjectId)
    details = FieldProperty(s.Anything, if_missing={})
    sort_weight = FieldProperty(s.Int, if_missing=0)
    ancestors = FieldProperty([{
        '_id': s.ObjectId(),
        'name': s.Anything(),
        'slug': s.String()
    }])

    @property
    def i18n_name(self):
        return self.name.get(preferred_language(), self.name.get(tg.config.lang))

    @property
    def name_with_ancestors(self):
        if not self.ancestors:
            return self.name[tg.config.lang]
        return "%s > %s" % (" > ".join([ancestor.name[tg.config.lang] for ancestor in self.ancestors]),
                             self.name[tg.config.lang])

    @classmethod
    def i18n_ancestor_name(cls, ancestor):
        return ancestor.name.get(preferred_language(), ancestor.name.get(tg.config.lang))

    @classmethod
    def previous(cls, category):
        category = cls.query.get(_id=ObjectId(category))
        return cls.query.find({'sort_weight': {'$lt': category.sort_weight}})\
            .sort([('sort_weight', DESCENDING)]).limit(2).all()

    @classmethod
    def subsequent(cls, category):
        category = cls.query.get(_id=ObjectId(category))
        return cls.query.find({'sort_weight': {'$gt': category.sort_weight}})\
            .sort([('sort_weight', ASCENDING)]).limit(2).all()


class Product(MappedClass):
    class __mongometa__:
        session = DBSession
        name = 'products'
        unique_indexes = [('slug',),
                          ('configurations.sku',)
                          ]
        indexes = [('type', 'active', ('valid_to', -1)),
                   ('type', 'category_id', 'active'),
                   ('type', 'active' 'name'),
                   ('type', 'active', ('sort_weight', -1)),
                   ('type', 'active', 'sort_weight'),
                   ('type', 'active', ('sort_category_weight', -1)),
                   ('type', 'active', 'sort_category_weight'),
                   ('type', 'published', 'active', ('sold', -1))]

    _id = FieldProperty(s.ObjectId)
    name = FieldProperty(s.Anything, required=True)
    type = FieldProperty(s.String, required=True)
    category_id = ForeignIdProperty(Category)
    category = RelationProperty(Category, via='category_id')
    categories_ids = ForeignIdProperty(Category, uselist=True)
    categories = RelationProperty(Category, via='categories_ids')
    description = FieldProperty(s.Anything, if_missing='')
    slug = FieldProperty(s.String, required=True)
    details = FieldProperty(s.Anything, if_missing={})
    active = FieldProperty(s.Bool, if_missing=True)
    published = FieldProperty(s.Bool, if_missing=True)
    valid_from = FieldProperty(s.DateTime)
    valid_to = FieldProperty(s.DateTime)
    sort_weight = FieldProperty(s.Int, if_missing=0)
    sort_category_weight = FieldProperty(s.Int, if_missing=0)
    sold = FieldProperty(s.Int, if_missing=0)
    configurations = FieldProperty([{
        'variety': s.Anything(required=True),
        'qty': s.Int(required=True),
        'initial_quantity': s.Int(required=True),
        'sku': s.String(required=True),
        'price': s.Float(required=True),
        'rate': s.Float(if_missing=0.0),
        'vat': s.Float(required=True),
        'details': s.Anything(if_missing={}),
    }])

    def min_price_configuration(self, min_qty_getter=1):
        if isinstance(min_qty_getter, str):
            min_qty_getter = operator.attrgetter(min_qty_getter)
        else:
            min_qty_getter = lambda c: min_qty_getter

        configurations_by_price = sorted(filter(lambda conf: conf[2]['qty'] >= min_qty_getter(conf[2]),
                                                map(lambda conf: (conf[0], conf[1]['price'] + conf[1]['vat'], conf[1]),
                                                    enumerate(self.configurations))),
                                         key=lambda x: x[1])
        if not configurations_by_price:
            return None, None

        return configurations_by_price[0][:2]

    @property
    def thumbnail(self):
        return tg.url(self.details['product_photos'][0]['url']) if self.details['product_photos'] else '//placehold.it/300x300'

    @property
    def i18n_name(self):
        return self.name.get(preferred_language(), self.name.get(tg.config.lang))

    @property
    def i18n_description(self):
        return self.description.get(preferred_language(), self.description.get(tg.config.lang))

    @property
    def available(self):
        if not self.active:
            return False

        for configuration in self.configurations:
            if configuration.qty > 0:
                return True

        return False

    def i18n_configuration_variety(self, configuration):
        return configuration.variety.get(preferred_language(), configuration.variety.get(tg.config.lang))

    def configuration_gross_price(self, configuration):
        return configuration.price + configuration.vat

    @classmethod
    def previous(cls, product):
        return cls.query.find({'sort_weight': {'$lt': product.sort_weight}}).\
                         sort([('sort_weight', DESCENDING)]).limit(2).all()

    @classmethod
    def previous_in_category(cls, product):
        return cls.query.find({'sort_category_weight': {'$lt': product.sort_category_weight}}).\
                         sort([('sort_category_weight', DESCENDING)]).limit(2).all()

    @classmethod
    def subsequent(cls, product):
        return cls.query.find({'sort_weight': {'$gt': product.sort_weight}}).\
                         sort([('sort_weight', ASCENDING)]).limit(2).all()

    @classmethod
    def subsequent_in_category(cls, product):
        return cls.query.find({'sort_category_weight': {'$gt': product.sort_category_weight}}).\
                         sort([('sort_category_weight', ASCENDING)]).limit(2).all()

    @classmethod
    def increase_sold(cls, sku, qty):
        DBSession.update(cls, {'configurations.sku': sku}, {'$inc': {'sold': qty}})

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
    last_update = FieldProperty(s.DateTime, if_missing=datetime.utcnow())
    order_info = FieldProperty({
        'payment': s.Anything(if_missing={}),
        'shipment_info': {
            'receiver': s.String(),
            'address': s.String(),
            'city': s.String(),
            'province': s.String(),
            'state': s.String(),
            'zip_code': s.String(),
            'country': s.String(),
            'details': s.Anything(if_missing={})
        },
        'currencies': {
            'due': s.Int,
            'shipping_charges': s.Int,
            'applied_discount': s.Int,
        },
        'shipping_charges': s.Float(if_missing=0.0),
        'applied_discount': s.Float(if_missing=0.0),
        'due': s.Float(if_missing=0.0),
        'bill': s.Bool(if_missing=False),
        'bill_info': {
            'company': s.String(),
            'vat': s.String(),
            'fiscal_code': s.String(if_missing=''),
            'address': s.String(),
            'city': s.String(),
            'province': s.String(),
            'state': s.String(),
            'zip_code': s.String(),
            'country': s.String(),
            'bill_emitted': s.Bool(if_missing=False),
            'details': s.Anything(if_missing={})
        },
        'discounts': s.Anything(if_missing=[]),
        'notes': s.String(),
        'message':s.String(),
        'details': s.Anything(if_missing={})
    })

    @property
    def order_due(self):
        currency_due = '%s' % self.order_info.currencies.due
        return '%s.%s' % (currency_due[:-2] or 0, currency_due[-2:])

    @property
    def item_count(self):
        return sum([item['qty'] for item in self.items.itervalues()])

    @property
    def subtotal(self):
        return sum([item['price']*item['qty'] for item in self.items.itervalues()])

    @property
    def tax(self):
        return sum([item['vat'] * item['qty'] for item in self.items.itervalues()])

    @property
    def total(self):
        return self.subtotal + self.tax

    @classmethod
    def items_subtotal(cls, item):
        return item['price'] * item['qty']

    @classmethod
    def items_vat(cls, item):
        return item['vat'] * item['qty']

    @classmethod
    def items_total(cls, item):
        return (item['price'] + item['vat']) * item['qty']

    @classmethod
    def expired_carts(cls):
        return cls.query.find({'expires_at': {'$lte': datetime.utcnow()}})



class OrderStatusExt(MapperExtension):
    def before_insert(self, instance, state, sess):
        status = instance.status or 'created'
        self._change_status(instance, status)
        self._store_user_name(instance)

    def before_update(self, instance, state, sess):
        if instance.status != self._prev_status(instance):
            self._change_status(instance, instance.status)

    def _change_status(self, instance, status):
        try:
            identity = tg.request.identity['user']
        except:
            identity = Bunch(name='Automatic', surname='Change', email_address='')
        changed_by = '%s %s' % (getattr(identity, 'name', identity.email_address), getattr(identity, 'surname', ''))\
            if identity else (None, None)
        instance.status_changes.append({'status': status, 'changed_by': changed_by, 'changed_at': datetime.utcnow()})

    def _prev_status(self, instance):
        return instance.status_changes[-1]['status']

    def _store_user_name(self, instance):
        user_id = instance.user_id
        user_obj = app_model.User.query.get(_id=ObjectId(user_id))
        user = '%s %s' % (getattr(user_obj, 'name', user_obj.email_address), getattr(user_obj, 'surname', ''))
        instance.user = user


class Order(MappedClass):
    class __mongometa__:
        session = DBSession
        name = 'orders'
        indexes = [('user_id', ),
                   ('status_changes.changed_at', ),
                   (('user', ), ('status_changes.changed_at', )),
                   (('status', ), ('status_changes.changed_at', )),
                   ('creation_date', )
                   ]
        extensions = [OrderStatusExt]

    _id = FieldProperty(s.ObjectId)
    user_id = FieldProperty(s.String, required=True)
    user = FieldProperty(s.String)
    payment_date = FieldProperty(s.DateTime, required=True)
    cancellation_date = FieldProperty(s.DateTime)
    creation_date = FieldProperty(s.DateTime, required=True)
    shipment_info = FieldProperty({
        'receiver': s.String(),
        'address': s.String(),
        'city': s.String(),
        'province': s.String(),
        'state': s.String(),
        'zip_code': s.String(),
        'country': s.String(),
        'details': s.Anything(if_missing={})
    })
    bill = FieldProperty(s.Bool, if_missing=False)
    billed = FieldProperty(s.Bool, if_missing=False)
    billed_date = FieldProperty(s.DateTime)
    billed_by = FieldProperty(s.String)
    bill_info = FieldProperty({
        'company': s.String(),
        'vat': s.String(),
        'fiscal_code': s.String(if_missing=''),
        'address': s.String(),
        'city': s.String(),
        'province': s.String(),
        'state': s.String(),
        'zip_code': s.String(),
        'country': s.String(),
        'bill_emitted': s.Bool(),
        'details': s.Anything(if_missing={})
    })
    payer_info = FieldProperty({
        'first_name': s.String(),
        'last_name': s.String(),
        'email': s.String()
    })
    items = FieldProperty([{
        'name': s.Anything(required=True),
        'category_name': s.Anything(if_missing={}),
        'variety': s.Anything(required=True),
        'qty': s.Int(required=True),
        'sku': s.String(required=True),
        'net_price': s.Float(required=True),
        'rate': s.Float(),
        'vat': s.Float(required=True),
        'base_rate': s.Float(),
        'base_vat': s.Float(required=True),
        'gross_price': s.Float(required=True),
        'details': s.Anything(if_missing={})
    }])
    currencies = FieldProperty({
        'due': s.Int,
        'shipping_charges': s.Int,
        'applied_discount': s.Int,
    })
    net_total = FieldProperty(s.Float, required=True)
    tax = FieldProperty(s.Float, required=True)
    gross_total = FieldProperty(s.Float, required=True)
    shipping_charges = FieldProperty(s.Float, required=True)
    total = FieldProperty(s.Float, required=True)
    due = FieldProperty(s.Float, if_missing=0.0)
    discounts = FieldProperty(s.Anything, if_missing=[])
    applied_discount = FieldProperty(s.Float, if_missing=0)
    status = FieldProperty(s.String, required=True)
    notes = FieldProperty(s.String, if_missing='')
    message = FieldProperty(s.String, if_missing='')
    payment_type = FieldProperty(s.String, if_missing='')
    details = FieldProperty(s.Anything, if_missing={})
    status_changes = FieldProperty(s.Anything, if_missing=[])

    @property
    def formatted_currencies(self):
        currencies = Bunch()
        for name, value in self.currencies.items():
            str_value = str(value)
            currencies[name] = '%s.%s' % (str_value[:-2], str_value[-2:])
        return currencies

    @property
    def net_per_vat_rate(self):
        def _item_discount_fraction(item, total):
            discount_chunk = self.applied_discount / total
            return int(item.gross_price * discount_chunk * 100)

        mapping = {}

        sorted_items = sorted(self.items, key=lambda i: i['rate'])
        for k, g in groupby(sorted_items, key=lambda i: i['rate']):
            mapping[k] = sum(imap(lambda i: (with_currency.float2cur(i.gross_price) + _item_discount_fraction(i, self.gross_total)) * i.qty, g))


        if self.currencies.due:
            # If we have currency values available, fix the rounding error
            current_total = sum(mapping.itervalues())
            expected_total = self.currencies.due - self.currencies.shipping_charges
            delta = expected_total - current_total
            mapping[sorted_items[-1]['rate']] += delta


        # Convert everything back to floats for visualization
        for k, g in mapping.iteritems():
            mapping[k] = with_currency.cur2float(g)

        return mapping

    @property
    def billed_by_name(self):
        user_obj = app_model.User.query.get(_id=ObjectId(self.billed_by))
        user = '%s %s' % (user_obj.name, user_obj.surname)
        return user

    @property
    def bill_country(self):
        if self.bill_info.get('country') is not None:
            return self.bill_info.get('country')
        else:
            return self.shipment_info.get('country')

    @classmethod
    def all_the_vats(cls):
        def aggregate_vats():
            vat_for_status = DBSession.impl.db.orders.aggregate([{'$project': {'items': 1, 'status': 1}},
                                                                 {'$unwind': '$items'},
                                                                 {'$group': {'_id': '$status',
                                                                             'vat_rates': {'$addToSet': '$items.rate'}}}])
            return sorted(set(chain(*[v['vat_rates'] for v in vat_for_status['result']])))
        vat_cache = cache.get_cache('all_the_vats')
        cachedvalue = vat_cache.get_value(
            key='42',
            createfunc=aggregate_vats,
            expiretime=3600*24*30  # one month
        )
        return cachedvalue


class Setting(MappedClass):
    class __mongometa__:
        session = DBSession
        name = 'ecommerce_settings'
        unique_indexes = [('setting', )]

    _id = FieldProperty(s.ObjectId)
    setting = FieldProperty(s.String)
    value = FieldProperty(s.Anything)

