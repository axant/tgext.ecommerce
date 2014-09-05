# coding=utf-8
from __future__ import unicode_literals
from collections import Counter
import re
from bson import ObjectId
import datetime
from ming import DESCENDING
from tgext.ecommerce.lib.exceptions import AlreadyExistingSkuException, AlreadyExistingSlugException, \
    InactiveProductException
from tgext.ecommerce.lib.utils import slugify, internationalise as i_, NoDefault, preferred_language, apply_vat
from tgext.ecommerce.model import models
from ming.odm import mapper
from tg import cache


class ProductManager(object):
    @classmethod
    def create(cls, type, sku, name, category_id=None, categories_ids=None, description='', price=1.0, rate=0.0,  #create_product
               vat=None, qty=0, initial_quantity=0, variety=None, active=True, published=False, valid_from=None,
               valid_to=None,
               configuration_details=None, **details):
        if variety is None:
            variety = name

        if configuration_details is None:
            configuration_details = {}

        if categories_ids is None:
            categories_ids = []

        slug = slugify(name, type, models)
        if models.Product.query.find({'slug': slug}).first():
            raise AlreadyExistingSlugException('Already exist a Product with slug: %s' % slug)

        if models.Product.query.find({'configurations.sku': sku}).first():
            raise AlreadyExistingSkuException('Already exist a Configuration with sku: %s' % sku)

        if vat is None:
            vat = apply_vat(price, rate)

        product = models.Product(type=type,
                                 name=i_(name),
                                 category_id=ObjectId(category_id) if category_id else None,
                                 categories_ids=categories_ids,
                                 description=i_(description),
                                 slug=slug,
                                 details=details,
                                 active=active,
                                 published=published,
                                 valid_from=valid_from,
                                 valid_to=valid_to,
                                 configurations=[{'sku': sku,
                                                  'variety': i_(variety),
                                                  'price': price,
                                                  'rate': rate,
                                                  'vat': vat,
                                                  'qty': qty,
                                                  'initial_quantity': initial_quantity,
                                                  'details': configuration_details}])
        models.DBSession.flush()
        return product

    @classmethod
    def create_configuration(cls, product, sku, price=1.0, rate=0.0, vat=None,
                             qty=0, initial_quantity=0, variety=None,
                             **configuration_details):

        if models.Product.query.find({'configurations.sku': sku}).first():
            raise AlreadyExistingSkuException('Already exist a Configuration with sku: %s' % sku)

        if vat is None:
            vat = apply_vat(price, rate)

        product.configurations.append({'sku': sku,
                                       'variety': i_(variety),
                                       'price': price,
                                       'rate': rate,
                                       'vat': vat,
                                       'qty': qty,
                                       'initial_quantity': initial_quantity,
                                       'details': configuration_details})

    @classmethod
    def get(cls, sku=None, _id=None, slug=None, query=None):  # get_product
        if query is None:
            query = {}
        if _id is not None:
            query.update({'_id': ObjectId(_id)})
            return models.Product.query.find(query).first()
        if sku is not None:
            query.update({'configurations.sku': sku})
            return models.Product.query.find(query).first()
        if slug is not None:
            query.update({'slug': slug})
            return models.Product.query.find(query).first()
        else:
            return None

    @classmethod
    def get_many(cls, type=None, query=None, fields=None):  # get_products
        if not query:
            query = dict()
        query.setdefault('published', {'$ne': False})  # backward compatibility
        filter = {}
        if type:
            filter['type'] = type
        filter.update(query)
        q_kwargs = {}
        if fields:
            q_kwargs['fields'] = fields
        q = models.Product.query.find(filter, **q_kwargs)
        return q

    @classmethod
    def get_bestsellers(cls):
        def _fetch_bestsellers():
            skus = []
            for product in cls.get_many('product', {'active': True}).sort([('sold', DESCENDING)]).limit(12).all():
                skus.append(product.configurations[0].sku)
            return skus

        bestselling_cache = cache.get_cache('bestselling_products')
        bestseller = bestselling_cache.get_value(key='bestseller',
                                                 expiretime=24 * 3600,
                                                 createfunc=_fetch_bestsellers)
        return bestseller

    @classmethod
    def edit(cls, product, type=NoDefault, name=NoDefault, category_id=NoDefault, categories_ids=NoDefault,
             description=NoDefault, valid_from=NoDefault, valid_to=NoDefault, **details):

        if product.active == False:
            raise InactiveProductException('Cannot edit an inactive product')

        if type is not NoDefault:
            product.type = type

        if name is not NoDefault:
            for k, v in i_(name).iteritems():
                setattr(product.name, k, v)

        if category_id is not NoDefault:
            product.category_id = ObjectId(category_id)

        if categories_ids is not NoDefault:
            product.categories_ids = categories_ids

        if description is not NoDefault:
            for k, v in i_(description).iteritems():
                setattr(product.description, k, v)

        if details is not {}:
            for k, v in details.iteritems():
                setattr(product.details, k, v)

        if valid_from is not NoDefault:
            product.valid_from = valid_from

        if valid_to is not NoDefault:
            product.valid_to = valid_to

    @classmethod
    def edit_configuration(cls, product, configuration_index, sku=NoDefault, variety=NoDefault,
                           price=NoDefault, rate=NoDefault, vat=NoDefault, qty=NoDefault,
                           initial_quantity=NoDefault, configuration_details=NoDefault):

        if sku is not NoDefault:
            product.configurations[configuration_index].sku = sku
        if variety is not NoDefault:
            for k, v in i_(variety).iteritems():
                setattr(product.configurations[configuration_index].variety, k, v)
        if price is not NoDefault:
            product.configurations[configuration_index].price = price
        if rate is not NoDefault:
            product.configurations[configuration_index].rate = rate
        if vat is not NoDefault:
            product.configurations[configuration_index].vat = vat
        if qty is not NoDefault:
            product.configurations[configuration_index].qty = qty
        if initial_quantity is not NoDefault:
            product.configurations[configuration_index].initial_quantity = initial_quantity
        if configuration_details is not NoDefault:
            for k, v in configuration_details.iteritems():
                setattr(product.configurations[configuration_index].details, k, v)

    @classmethod
    def delete(cls, product):  # delete_product
        product.active = False

    @classmethod
    def publish(cls, product, published=True):
        product.published = published

    @classmethod
    def sort_up(cls, product):
        subsequent = models.Product.subsequent(product)
        try:
            little_weight = subsequent[0].sort_weight
        except:
            little_weight = 0

        try:
            big_weight = subsequent[1].sort_weight
        except:
            big_weight = little_weight + 20000

        product.sort_weight = little_weight + (big_weight-little_weight)/2

    @classmethod
    def sort_up_in_category(cls, product):
        subsequent = models.Product.subsequent_in_category(product)
        try:
            little_weight = subsequent[0].sort_category_weight
        except:
            little_weight = 0

        try:
            big_weight = subsequent[1].sort_category_weight
        except:
            big_weight = little_weight + 20000

        product.sort_category_weight = little_weight + (big_weight-little_weight)/2

    @classmethod
    def sort_down(cls, product):
        previous = models.Product.previous(product)
        try:
            big_weight = previous[0].sort_weight
        except:
            big_weight = 0

        try:
            little_weight = previous[1].sort_weight
        except:
            little_weight = big_weight - 20000

        product.sort_weight = little_weight + (big_weight-little_weight)/2

    @classmethod
    def sort_down_in_category(cls, product):
        previous = models.Product.previous_in_category(product)
        try:
            big_weight = previous[0].sort_category_weight
        except:
            big_weight = 0

        try:
            little_weight = previous[1].sort_category_weight
        except:
            little_weight = big_weight - 20000

        product.sort_category_weight = little_weight + (big_weight-little_weight)/2

    @classmethod
    def sort_before_other(cls, product_to_sort, other_product):
        subsequent = models.Product.subsequent(other_product)
        little_weight = other_product.sort_weight
        try:
            big_weight = subsequent[0].sort_weight
        except:
            big_weight = little_weight + 20000

        product_to_sort.sort_weight = little_weight + (big_weight-little_weight)/2

    @classmethod
    def sort_before_other_in_category(cls, product_to_sort, other_product):
        subsequent = models.Product.subsequent_in_category(other_product)
        little_weight = other_product.sort_category_weight
        try:
            big_weight = subsequent[0].sort_category_weight
        except:
            big_weight = little_weight + 20000

        product_to_sort.sort_category_weight = little_weight + (big_weight-little_weight)/2

    @classmethod
    def buy(cls, cart, product, configuration_index, amount):  #buy_product
        sku = product.configurations[configuration_index]['sku']
        product_in_cart = cart.items.get(sku, {})
        already_bought = product_in_cart.get('qty', 0)
        total_qty = already_bought + amount

        quantity_field = 'configurations.%s.qty' % configuration_index
        result = models.DBSession.impl.update_partial(mapper(models.Product).collection,
                                                      {'_id': product._id,
                                                       quantity_field: {'$gte': amount}},
                                                      {'$inc': {quantity_field: -amount}})
        bought = result.get('updatedExisting', False)

        if bought:
            cls._add_to_cart(cart, cls._product_dump(product, configuration_index), total_qty)

        return bought

    def get_suggested_for_user(self, user_id, limit=5):  #get_suggested_products_per_user
        """Gives a list of suggested sku products based on the past orders of a user

        :param user_id: the user id string to get suggestions for
        :param limit: optional max number of suggestions (default to 5)
        """
        past_orders = models.Order.query.find({'user_id': user_id})
        skus = Counter([item.sku for order in past_orders for item in order.items])
        suggested_skus = [t[0] for t in skus.most_common(limit)]
        offers_placeholders = len(suggested_skus) - limit
        if offers_placeholders:
            offers = self.get_many('product', {'active': True},
                                   fields=['name', 'type', 'configurations', 'slug', 'details'])\
                .sort([('valid_to', -1)]).limit(offers_placeholders)
            suggested_skus.extend([offer.configurations[0].sku for offer in offers])

        return suggested_skus  # filter just the sku without the frequency

    @classmethod
    def _config_idx(cls, product, sku):
        return [i for i, config in enumerate(product['configurations']) if config['sku'] == sku][0]

    @classmethod
    def _product_dump(cls, product, configuration_index=None, sku=None):
        """Normalize product and configuration in a single level dict

        :param product: product mapped object
        :param configuration_index: configuration index
        """
        assert configuration_index is not None or sku
        if configuration_index is None:
            configuration_index = cls._config_idx(product, sku)
        config = product['configurations'][configuration_index]

        return dict(
            name=product.name,
            category_name=product.category.name if product.category is not None else '',
            description=product.description,
            product_details=product.details,
            base_vat=config.get('vat', 0.0),
            base_rate=config.get('rate', 0.0),
            **config
        )

    @classmethod
    def _add_to_cart(cls, cart, product_dump, qty):
        sku = product_dump['sku']
        cart.last_update = datetime.datetime.utcnow()
        if qty == 0:
            cart.items.pop(sku, None)
        else:
            product_dump['qty'] = qty
            cart.items[sku] = product_dump

    @classmethod
    def search(cls, text, fields=('name', 'description'), language=None):
        language = language or preferred_language()
        filters = []
        for field in fields:
            field = '%s.%s' % (field, language)
            filters.append({field: re.compile(text, re.I)})
        products = models.Product.query.find({'$or': filters, 'published': {'$ne': False}, 'active': {'$ne': False}})
        return products