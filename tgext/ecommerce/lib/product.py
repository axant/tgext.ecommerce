# coding=utf-8
from __future__ import unicode_literals
from collections import Counter
from bson import ObjectId
import datetime
from tgext.ecommerce.lib.exceptions import AlreadyExistingSkuException, AlreadyExistingSlugException, \
    InactiveProductException
from tgext.ecommerce.lib.utils import slugify, internationalise as i_, NoDefault
from tgext.ecommerce.model import models
from ming.odm import mapper


class ProductManager(object):
    @classmethod
    def create(cls, type, sku, name, category_id=None, description='', price=1.0,  #create_product
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

        product = models.Product(type=type,
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
        return product

    @classmethod
    def create_configuration(cls, product, sku, price=1.0, vat=0.0, #create_product_configuration
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

    @classmethod
    def get(cls, sku=None, _id=None, slug=None): #get_product
        if _id is not None:
            return models.Product.query.get(_id=ObjectId(_id))
        elif sku is not None:
            return models.Product.query.find({'configurations.sku': sku}).first()
        elif slug is not None:
            return models.Product.query.find({'slug': slug}).first()
        else:
            return None

    @classmethod
    def get_many(cls, type, query=None, fields=None): #get_products
        filter = {'type': type}
        filter.update(query or {})
        q_kwargs = {}
        if fields:
            q_kwargs['fields'] = fields
        q = models.Product.query.find(filter, **q_kwargs)
        return q

    @classmethod
    def edit(cls, product, type=NoDefault, name=NoDefault, category_id=NoDefault, #edit_product
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
    def edit_configuration(cls, product, configuration_index, sku=NoDefault, variety=NoDefault, #edit_product_configuration
                                   price=NoDefault, vat=NoDefault, qty=NoDefault,
                                   initial_quantity=NoDefault, configuration_details=NoDefault):

        if sku is not NoDefault:
            product.configurations[configuration_index].sku = sku
        if variety is not NoDefault:
            for k, v in i_(variety).iteritems():
                setattr(product.configurations[configuration_index].variety, k, v)
        if price is not NoDefault:
            product.configurations[configuration_index].price = price
        if vat is not NoDefault:
            product.configurations[configuration_index].vat = vat
        if qty is not NoDefault:
            product.configurations[configuration_index].qty = qty
        if initial_quantity is not NoDefault:
            product.configurations[configuration_index].initial_quantity = initial_quantity
        for k, v in configuration_details.iteritems():
            setattr(product.configurations[configuration_index].details, k, v)

    @classmethod
    def delete(cls, product): #delete_product
        product.active = False

    @classmethod
    def buy(cls, cart, product, configuration_index, amount): #buy_product
        sku = product.configurations[configuration_index]['sku']
        product_in_cart = cart.items.get(sku, {})
        already_bought = product_in_cart.get('qty', 0)
        total_qty = already_bought+amount

        quantity_field = 'configurations.%s.qty' % configuration_index
        result = models.DBSession.impl.update_partial(mapper(models.Product).collection,
                                                      {'_id': product._id,
                                                       quantity_field: {'$gte': amount}},
                                                      {'$inc': {quantity_field: -amount}})
        bought = result.get('updatedExisting', False)

        if bought:
            cls._add_to_cart(cart, cls._product_dump(product, configuration_index), total_qty)

        return bought

    def get_suggested_for_user(self, user_id, limit=5): #get_suggested_products_per_user
        """Gives a list of suggested sku products based on the past orders of a user

        :param user_id: the user id string to get suggestions for
        :parmas limit: optional max number of suggestions (default to 5)
        """
        past_orders = models.Order.query.find({'user_id': user_id})
        skus = Counter([item.sku for order in past_orders for item in order.items])
        suggested_skus = skus.most_common(limit)
        return [t[0] for t in suggested_skus]  # filter just the sku without the frequency

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
            description=product.description,
            product_details=product.details,
            base_vat=config.get('vat', 0),
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