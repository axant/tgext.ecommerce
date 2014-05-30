# coding=utf-8
from __future__ import unicode_literals

import tg

def format_price(price):
    return ('%0.3f' % price)[0:-1]