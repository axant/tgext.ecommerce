# coding=utf-8
from __future__ import unicode_literals

import tg
import paypalrestsdk

paypalrestsdk.configure({
  "mode": "sandbox", # sandbox or live
  "client_id": "AfOarBB0asXM-rUIkPcJWZHznMlre38CV0ZYudX0Lv2cVujzNGDgE4u7aZAT",
  "client_secret": "EKxWWhA9m2tTPStb57Y73vaA8wbnmNKXY93GYPd6Kk_KHdagyqTetEd7UTVW"})


def pay(cart, redirection):
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
        "payment_method": "paypal"
        },
        "redirect_urls": {
        "return_url": redirection,
        "cancel_url": "http://localhost:3000/cancel"
        },
        "transactions": [{
                          "item_list": {
        "items": [{
                      "name": "item",
                   "sku": "item",
                   "price": "60.00",
                   "currency": "EUR",
                   "quantity": 3 }]},
        "amount": {
        "total": "180.00",
        "currency": "EUR"},
        "description": "This is the payment transaction description."}]})

    if payment.create():
        cart.payment = {'backend': 'paypal',
                        'id': payment.id}

        for link in payment.links:
            if link.rel == "approval_url":
                print 'LINK', link.href
                return link.href

    return None


def confirm(cart, redirection, data):
    payerId = data['PayerID']
    return tg.url(redirection, qualified=True, params={'payer_id': payerId})


def execute(cart, data):
    paymentId = cart.payment['id']

    print 'PAYER: %s, PAYMENT: %s' % (data, paymentId)
    payment = paypalrestsdk.Payment.find(paymentId)
    print 'PAYMENT', payment

    return payment.execute(data)
