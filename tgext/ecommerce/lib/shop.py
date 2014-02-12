import sys
import datetime
import tg
from tgext.ecommerce.lib.exceptions import AlreadyExistingSlugException, AlreadyExistingSkuException, \
    CategoryAssignedToProductException, InactiveProductException
from tgext.ecommerce.lib.payments import paypal
from tgext.ecommerce.lib.utils import slugify, internationalise as i_
from tgext.ecommerce.model import models
from bson import ObjectId
from ming.odm import mapper


class NoDefault(object):
    """A dummy value used for parameters with no default."""


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

    def get_products(self, type, query=None, fields=None):
        filter = {'type': type}
        filter.update(query or {})
        q_kwargs = {}
        if fields:
            q_kwargs['fields'] = fields
        q = models.Product.query.find(filter, **q_kwargs)
        return q

    def edit_product(self, product, type=NoDefault, name=NoDefault, category_id=NoDefault,
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


    def edit_product_configuration(self, product, configuration_index, sku=NoDefault, variety=NoDefault,
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

    def delete_product(self, product):
        product.active = False

    def _config_idx(self, product, sku):
        return [i for i, config in enumerate(product['configurations']) if config['sku'] == sku][0]

    def _product_dump(self, product, configuration_index=None, sku=None):
        """Normalize product and configuration in a single level dict

        :param product: product mapped object
        :param configuration_index: configuration index
        """
        assert configuration_index is not None or sku
        if configuration_index is None:
            configuration_index = self._config_idx(product, sku)
        config = product['configurations'][configuration_index]

        return dict(
            name=product.name,
            description=product.description,
            product_details=product.details,
            **config
        )

    def _add_to_cart(self, cart, product_dump, qty):
        sku = product_dump['sku']
        cart.last_update = datetime.datetime.utcnow()
        if qty == 0:
            cart.items.pop(sku, None)
        else:
            product_dump['qty'] = qty
            cart.items[sku] = product_dump

    def buy_product(self, cart, product, configuration_index, amount):
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
            self._add_to_cart(cart, self._product_dump(product, configuration_index), total_qty)

        return bought

    def create_category(self, name):
        category = models.Category(name=i_(name))
        models.DBSession.flush()
        return category

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

    def get_cart(self, user_id):
        return models.Cart.query.find({'user_id': user_id}).first()

    def create_or_get_cart(self, user_id):
        cart = self.get_cart(user_id)
        if cart is None:
            cart = models.Cart(user_id=user_id)
            models.DBSession.flush()
        return cart

    def delete_from_cart(self, cart, sku):
        return self.update_cart_item_qty(cart, sku, 0)

    def update_cart_item_qty(self, cart, sku, qty):
        product_in_cart = cart.items.get(sku, {})
        already_bought = product_in_cart.get('qty', 0)
        delta_qty = qty - already_bought
        if delta_qty == 0:
            return cart
        product = self.get_product(sku=sku)
        self.buy_product(cart, product, self._config_idx(product, sku), delta_qty)
        return cart

    def pay(self, cart, redirection_url, cancel_url, shipping_charges=0):
        return paypal.pay(cart, redirection_url, cancel_url, shipping_charges)

    def confirm(self, cart, redirection, data):
        return paypal.confirm(cart, redirection, data)

    def execute(self, cart, data):
        return paypal.execute(cart, data)