# coding=utf-8
from __future__ import unicode_literals

import tg
import paypalrestsdk

paypalrestsdk.configure({
  "mode": "sandbox", # sandbox or live
  "client_id": "AfOarBB0asXM-rUIkPcJWZHznMlre38CV0ZYudX0Lv2cVujzNGDgE4u7aZAT",
  "client_secret": "EKxWWhA9m2tTPStb57Y73vaA8wbnmNKXY93GYPd6Kk_KHdagyqTetEd7UTVW"})


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

    print shipping_charges
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
                              "total": cart.total + shipping_charges,
                              "currency": "EUR",
                              "details": {
                                  "shipping": "%0.2f" % shipping_charges,
                                  "subtotal": cart.subtotal,
                                  "tax": cart.tax
                              }
                          },
                          }]
    })

    if payment.create():
        cart.payment = {'backend': 'paypal',
                        'id': payment.id}

        for link in payment.links:
            if link.rel == "approval_url":
                print 'LINK', link.href
                return link.href
    else:
        print 'PAYMENT ERROR', payment.error
        return cancel_url



def confirm(cart, redirection, data):
    payerId = data['PayerID']
    return tg.url(redirection, qualified=True, params={'payer_id': payerId})


def execute(cart, data):
    paymentId = cart.payment['id']

    print 'PAYER: %s, PAYMENT: %s' % (data, paymentId)
    payment = paypalrestsdk.Payment.find(paymentId)
    print 'PAYMENT', payment

    return payment.execute(data)
