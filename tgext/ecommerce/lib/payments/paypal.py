# coding=utf-8
from __future__ import unicode_literals

import tg
import paypalrestsdk
import datetime
import math
from tgext.ecommerce.lib.utils import apply_percentage_discount, get_percentage_discount


def configure_paypal(mode, client_id, client_secret):
    paypalrestsdk.configure({
        "mode": mode,
        "client_id": client_id,
        "client_secret": client_secret})


def pay(cart, redirection_url, cancel_url):
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": redirection_url,
            "cancel_url": cancel_url
        },
        "transactions": [{"item_list": {"items": [{"name": "Order %s" % str(cart._id),
                                                   "price": cart.order_due,
                                                   "sku": str(cart._id),
                                                   "currency": "EUR",
                                                   "quantity": 1}]},
                          "amount": {
                              "total": cart.order_due,
                              "currency": "EUR",
                          }}]
    })

    if payment.create():
        cart.order_info.payment = {'backend': 'paypal',
                                   'id': payment.id,
                                   'date': datetime.datetime.utcnow()}

        for link in payment.links:
            if link.rel == "approval_url":
                return link.href
    else:
        print payment.error
        return cancel_url


def confirm(cart, redirection, data):
    payerId = data['PayerID']
    return tg.url(redirection, qualified=True, params={'payer_id': payerId})


def execute(cart, data):
    paymentId = cart.order_info.payment['id']
    payment = paypalrestsdk.Payment.find(paymentId)
    result = payment.execute(data)
    payer_info = dict()
    if result:
        payer_info['first_name'] = payment.payer.payer_info.first_name
        payer_info['last_name'] = payment.payer.payer_info.last_name
        payer_info['email'] = payment.payer.payer_info.email

    return dict(result=result, payer_info=payer_info)

