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


def pay(cart, redirection_url, cancel_url, shipping_charges):
    raw_items = [v for k, v in cart.items.iteritems()]
    items = []
    for item in raw_items:
        item_name = item.name.get(tg.translator.preferred_language, item.name.get(tg.config.lang))
        item_variety = item.variety.get(tg.translator.preferred_language, item.variety.get(tg.config.lang))
        item = {"name": "%s, %s" % (item_name, item_variety),
                "sku": item.sku,
                "price": item.price,
                "currency": "EUR",
                "quantity": item.qty}
        items.append(item)

    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": redirection_url,
            "cancel_url": cancel_url
        },
        "transactions": [{"item_list": {"items": items},
                          "amount": {
                              "total": "%0.2f" % (cart.total + shipping_charges),
                              "currency": "EUR",
                              "details": {
                                  "shipping": "%0.2f" % shipping_charges,
                                  "subtotal": "%0.2f" % cart.subtotal,
                                  "tax":   "%0.2f" % cart.tax
                              }
                          },
                          }]
    })

    if payment.create():
        cart.payment = {'backend': 'paypal',
                        'id': payment.id,
                        'timestamp': datetime.datetime.utcnow()}

        for link in payment.links:
            if link.rel == "approval_url":
                return link.href
    else:
        return cancel_url


def confirm(cart, redirection, data):
    payerId = data['PayerID']
    return tg.url(redirection, qualified=True, params={'payer_id': payerId})


def execute(cart, data):
    paymentId = cart.payment['id']
    payment = paypalrestsdk.Payment.find(paymentId)
    return payment.execute(data)
