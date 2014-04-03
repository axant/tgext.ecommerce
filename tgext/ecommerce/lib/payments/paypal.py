# coding=utf-8
from __future__ import unicode_literals

import tg
import paypalrestsdk
import datetime


def configure_paypal(mode, client_id, client_secret):
    paypalrestsdk.configure({
        "mode": mode,
        "client_id": client_id,
        "client_secret": client_secret})


def pay(cart, redirection_url, cancel_url):
    total_discount = 0
    for discount in cart.order_info.get('discounts', {}).values():
        if isinstance(discount, dict) and discount['type'] == 'percentage':
            qty = -(discount['qty'] / 100.0) * cart.total
        elif isinstance(discount, dict) and discount['type'] == 'fixed':
            qty = -discount['qty']
        else:
            qty = 0
        total_discount += qty

    cart.order_info.setdefault('discounts', {})
    cart.order_info['discounts']['applied_discount'] = total_discount

    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": redirection_url,
            "cancel_url": cancel_url
        },
        "transactions": [{"item_list": {"items": [{"name": "Tavolaclandestina",
                                                   "price": '%0.2f' % (cart.total + cart.order_info.shipping_charges +
                                                                       total_discount),
                                                   "sku": 'TC',
                                                   "currency": "EUR",
                                                   "quantity": 1}]},
                          "amount": {
                              "total": "%0.2f" % (cart.total + cart.order_info.shipping_charges + total_discount),
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

