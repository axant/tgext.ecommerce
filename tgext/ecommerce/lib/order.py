# coding=utf-8
from __future__ import unicode_literals
from bson import ObjectId
import datetime
from tgext.ecommerce.model import models


class OrderManager(object):
    @classmethod
    def create(cls, cart, items, shipping_charges=0.0, payment_date=None, shipment_info=None,  #create_order
               bill=False, bill_info=None, payer_info=None, status='created', **details):
        if shipment_info is None:
            shipment_info = {}
        if bill_info is None:
            bill_info = {}
        if payer_info is None:
            payer_info = {}

        order = models.Order(_id=cart._id,
                             user_id=cart.user_id,
                             payment_date=payment_date,
                             creation_date=datetime.datetime.utcnow(),
                             shipment_info=shipment_info,
                             bill=bill,
                             bill_info=bill_info,
                             payer_info=payer_info,
                             items=items,
                             net_total=cart.subtotal,
                             tax=cart.tax,
                             gross_total=cart.total,
                             shipping_charges=shipping_charges,
                             total=cart.total+shipping_charges,
                             status=status,
                             details=details)

        models.DBSession.flush()
        return order

    @classmethod
    def get(self, _id): #get_order
        return models.Order.query.get(_id=ObjectId(_id))

    @classmethod
    def get_user_orders(self, user_id):
        """Retrieves all the past orders of a given user

        :param user_id: the user id string to filter for
        """
        return models.Order.query.find({'user_id': user_id})
