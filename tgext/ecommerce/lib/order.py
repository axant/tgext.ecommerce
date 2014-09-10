# coding=utf-8
from __future__ import unicode_literals
from bson import ObjectId
import datetime
from tgext.ecommerce.model import models, Product
from tgext.ecommerce.lib.utils import apply_vat, with_currency


class OrderManager(object):
    @classmethod
    def create(cls, cart, payment_date=None, payer_info=None, status='created', payment_type=None, **details): #create_order

        if payer_info is None:
            payer_info = {}

        if not payment_type:
            payment_type = ''

        items = []
        for cart_item in cart.items.values():
            items.append(dict(name=cart_item.get('name'), variety=cart_item.get('variety'),
                              category_name=cart_item.get('category_name', {}), qty=cart_item.get('qty'),
                              sku=cart_item.get('sku'), net_price=cart_item.get('price'), vat=cart_item.get('vat'),
                              rate=cart_item.get('rate'), gross_price=cart_item.get('price') + cart_item.get('vat'),
                              base_vat=cart_item.get('base_vat'), base_rate=cart_item.base_rate,
                              details=dict(cart_item.get('product_details').items()+cart_item.get('details').items())))
            Product.increase_sold(cart_item.get('sku'), qty=cart_item.get('qty'))

        order = models.Order(_id=cart._id,
                             user_id=cart.user_id,
                             payment_date=payment_date,
                             creation_date=datetime.datetime.utcnow(),
                             shipment_info=cart.order_info.shipment_info,
                             bill=cart.order_info.bill,
                             bill_info=cart.order_info.bill_info or {},
                             payer_info=payer_info,
                             items=items,
                             payment_type=payment_type,
                             net_total=cart.subtotal,
                             tax=cart.tax,
                             gross_total=cart.total,
                             shipping_charges=cart.order_info.shipping_charges,
                             total=cart.total+cart.order_info.shipping_charges,
                             due=cart.order_info.due,
                             discounts=cart.order_info.discounts,
                             applied_discount= - cart.order_info.applied_discount,
                             status=status,
                             notes=cart.order_info.notes,
                             message=cart.order_info.message,
                             details=details,
                             currencies=cart.order_info.currencies)
        cart.delete()
        models.DBSession.flush()
        return order

    @classmethod
    def get(self, _id): #get_order
        return models.Order.query.get(_id=ObjectId(_id))

    @classmethod
    def get_many(cls, query=dict(), fields=None): #get_products
        q_kwargs = {}
        if fields:
            q_kwargs['fields'] = fields
        q = models.Order.query.find(query, **q_kwargs)
        return q

    @classmethod
    def get_user_orders(self, user_id):
        """Retrieves all the past orders of a given user

        :param user_id: the user id string to filter for
        """
        return models.Order.query.find({'user_id': user_id})
