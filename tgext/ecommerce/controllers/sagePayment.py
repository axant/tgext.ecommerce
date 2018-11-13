# coding=utf-8
from __future__ import unicode_literals
from datetime import date, datetime
from itertools import groupby
from bson import ObjectId
from tg import TGController, hooks, expose, validate, lurl, redirect, request, tmpl_context, config, flash, predicates
class SagePaymentController(TGController):

    #Default page to request for the Card Info
    @expose('tgext.ecommerce.templates.sage_pay')
    def sage_pay(self, **kw):
        return dict(
            merchantSessionKey=kw['merchantSessionKey'],
            redirectionUrl=kw['redirectionUrl'],
            sage_API=config.get('sage_API'),
        )


    #Bridge page
    @expose('tgext.ecommerce.templates.sage_payment_card')
    def sage_pay_payment(self, **kw):
        return dict(
            acsUrl=kw['acsUrl'],
            paReq=kw['paReq'],
            TermUrl=kw['TermUrl'],
            MD=kw['MD'],
            sage_API=config.get('sage_API'),
        )

