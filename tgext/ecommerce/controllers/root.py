# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import TGController, expose, flash, require, url, lurl, request, redirect, validate, hooks, config, abort
from tg.i18n import ugettext as _, lazy_ugettext as l_

from tgext.ecommerce import model
from tgext.ecommerce.controllers.manage import ManageController
import json
import requests
from bson import ObjectId

class RootController(TGController):
    manage = ManageController()

    @expose('tgext.ecommerce.templates.sage_pay')
    def sage_pay(self, **kw):
        return dict(merchantSessionKey=kw['merchantSessionKey'], redirectionUrl=kw['redirectionUrl'])

    @expose('tgext.ecommerce.templates.sage_payment_card')
    def sage_pay_payment(self, **kw):
        return dict(acsUrl=kw['acsUrl'],paReq=kw['paReq'],TermUrl=kw['TermUrl'],MD=kw['MD'])

    @expose('tgext.ecommerce.templates.3DSStatus')
    def secure_3ds_handler(self, **kw):
        headers = {
            'Authorization': config['sage_header'],
            "Content-Type": "application/json",
        }

        cart = model.Cart.query.get(_id=ObjectId(kw['MD']))
        url = config['sage_API'] + 'transactions/' + str(cart.order_info.payment.transactionId) + '/3d-secure'
        response = requests.post(url, headers=headers, data=json.dumps(dict(paRes=kw['PaRes'])))
        response_obj = json.loads(response.text)
        hooks.notify("ecommerce.after_secure_3ds_sage_handler", args=(response_obj,cart))

        if response_obj.get('status'):
            if response_obj['status'] == "Authenticated":
                url = config['sage_API'] + 'transactions/' + str(cart.order_info.payment.transactionId)
                response = requests.get(url, headers=headers)
                response_obj = json.loads(response.text)
            return dict(status=response_obj['status'])
        else:
            return dict(status=str(response_obj['code']) + " " + str(response_obj['description']))



