# coding=utf-8
from __future__ import unicode_literals
from datetime import date, datetime
from itertools import groupby
from bson import ObjectId
from tg import TGController, hooks, expose, validate, lurl, redirect, request, tmpl_context, config, flash, predicates
from tg.i18n import lazy_ugettext as l_
import tw2.core as twc
import tw2.forms as twf
from tgext.ecommerce import model
from tw2.forms.widgets import BaseLayout
from tgext.ecommerce.lib import get_edit_order_form
from tgext.ecommerce.model import Order

import requests, json
class SagePaymentController(TGController):
    @expose('tgext.ecommerce.templates.sage_pay')
    def sage_pay(self, **kw):
        return dict(merchantSessionKey=kw['merchantSessionKey'], redirectionUrl=kw['redirectionUrl'])

    @expose('tgext.ecommerce.templates.sage_payment_card')
    def sage_pay_payment(self, **kw):
        return dict(acsUrl=kw['acsUrl'], paReq=kw['paReq'], TermUrl=kw['TermUrl'], MD=kw['MD'])

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
        hooks.notify("ecommerce.after_secure_3ds_sage_handler", args=(response_obj, cart))

        if response_obj.get('status'):
            if response_obj['status'] == "Authenticated":
                url = config['sage_API'] + 'transactions/' + str(cart.order_info.payment.transactionId)
                response = requests.get(url, headers=headers)
                response_obj = json.loads(response.text)
            return dict(status=response_obj['status'])
        else:
            return dict(status=str(response_obj['code']) + " " + str(response_obj['description']))

