# coding=utf-8
from __future__ import unicode_literals
from bson import ObjectId
import datetime
from tgext.ecommerce.model import models


class OrderManager(object):
    @classmethod
    def create(cls, cart, payment_date=None, payer_info=None, status='created', **details): #create_order

        if payer_info is None:
            payer_info = {}

        cart_items = [v for k, v in cart.items.iteritems()]
        items = [dict(name=cart_item.get('name'), variety=cart_item.get('variety'), qty=cart_item.get('qty'),
                      sku=cart_item.get('sku'), net_price=cart_item.get('price'), vat=cart_item.get('vat'),
                      gross_price=cart_item.get('price') * (1+cart_item.get('vat')),base_vat=cart_item.get('base_vat'),
                      details=cart_item.get('product_details'))
                 for cart_item in cart_items]

        order = models.Order(_id=cart._id,
                             user_id=cart.user_id,
                             payment_date=payment_date,
                             creation_date=datetime.datetime.utcnow(),
                             shipment_info=cart.order_info.shipment_info,
                             bill=cart.order_info.bill,
                             bill_info=cart.order_info.bill_info or {},
                             payer_info=payer_info,
                             items=items,
                             net_total=cart.subtotal,
                             tax=cart.tax,
                             gross_total=cart.total,
                             shipping_charges=cart.order_info.shipping_charges,
                             total=cart.total+cart.order_info.shipping_charges,
                             status=status,
                             notes=cart.order_info.notes,
                             details=details)
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
