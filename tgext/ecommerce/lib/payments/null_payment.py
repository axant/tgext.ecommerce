# coding=utf-8
from __future__ import unicode_literals

import tg
import datetime
import math
from tgext.ecommerce.lib.utils import apply_percentage_discount, get_percentage_discount



def pay(cart, redirection_url, cancel_url):
    cart.order_info.payment = {'backend': 'null_payment',
                               'id': cart._id,
                               'date': datetime.datetime.utcnow()}
    return redirection_url


def confirm(cart, redirection, data):
    return tg.url(redirection, qualified=True)


def execute(cart, data):
    return dict(result=dict({'result': 'payed'}), payer_info={})

