# coding=utf-8
from __future__ import unicode_literals

from tg import config, url, redirect
import paypalrestsdk
import datetime
import math
from tgext.ecommerce.lib.utils import apply_percentage_discount, get_percentage_discount

import requests, json
import tg
HEADERS={
        'Authorization': str(config['sage_header']),
        'Content-type': 'application/json',
}

def pay(cart, redirection_url, cancel_url):

    data = {"vendorName": config['sage_mode']}
    response = requests.post(config['sage_API'] + 'merchant-session-keys', headers=HEADERS, data=json.dumps(data))
    response_obj = json.loads(response.text)

    cart.order_info.payment = {'backend': 'sage',
                               'id': response_obj['merchantSessionKey'],
                               'date': datetime.datetime.utcnow()}

    return url('/shop/sage/sage_pay', qualified=True, params={'redirectionUrl': str(redirection_url), 'merchantSessionKey': response_obj['merchantSessionKey'], })

def confirm(cart, redirection, data):
    cart.order_info.payment.card_identifier = data["card-identifier"]
    return url(redirection, qualified=True)

def execute(cart, data):
    dataReq = {
        "transactionType": "Payment",
        "paymentMethod": {
            "card": {
                "merchantSessionKey" : str(cart.order_info.payment.id),
                "cardIdentifier": str(cart.order_info.payment.card_identifier),
            }
        },
        "vendorTxCode":  data['last_name'] +
                        str(datetime.datetime.utcnow().strftime('%b%d%Y%H%M%S')),
        "amount": cart.order_info.currencies.due,
        "currency": "GBP",
        "description": "London Trade Art - Shop",
        "apply3DSecure": config['sage_apply_3ds'],
        "customerFirstName": data['first_name'],
        "customerLastName": data['last_name'],
        "billingAddress": {
            "address1": str(cart.order_info.shipment_info.address),
            "city": str(cart.order_info.shipment_info.city),
            "postalCode": str(cart.order_info.shipment_info.zip_code),
            "country": str(cart.order_info.shipment_info.country),
        },
        "entryMethod": "Ecommerce"
    }
    response = requests.post(config['sage_API'] + 'transactions', headers=HEADERS, data=json.dumps(dataReq))
    response_obj = json.loads(response.text)

    if response_obj.get('status'):
        cart.order_info.payment.transactionId = response_obj['transactionId']

        if response_obj['status'] == "Ok":
            url = config['sage_API'] + 'transactions/' + str(cart.order_info.payment.transactionId)
            response = requests.get(url, headers=HEADERS)
            response_payer = json.loads(response.text)
            return dict(response=response_payer)

        elif response_obj['status'] == "3DAuth":
            redirect( tg.url('/shop/sage/sage_pay_payment'),
                    params={
                        'acsUrl': response_obj['acsUrl'],
                        'paReq': response_obj["paReq"],

                        'TermUrl': str(config['sage_webhook']) + data['redirect_url'],
                        'MD': str(cart._id)
                    })

    if response_obj.get('code'):
        return dict(error=str(response_obj['code']) + " " + str(response_obj['description']))
    else:
        return dict(error=response_obj)

def secure_3d(cart, data):

    url = config['sage_API'] + 'transactions/' + str(cart.order_info.payment.transactionId) + '/3d-secure'
    response = requests.post(url, headers=HEADERS, data=json.dumps(dict(paRes=data['PaRes'])))
    response_obj = json.loads(response.text)

    if response_obj.get('status'):
        if response_obj['status'] == "Authenticated":
            url = config['sage_API'] + 'transactions/' + str(cart.order_info.payment.transactionId)
            response = requests.get(url, headers=HEADERS)
            response_obj = json.loads(response.text)

        return dict(response=response_obj)
    elif response_obj.get('code'):
        return dict(error=str(response_obj['code']) + " " + str(response_obj['description']))
    else:
        return dict(error="Unknown Reason")

