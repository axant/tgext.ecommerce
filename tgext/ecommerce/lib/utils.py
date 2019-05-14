import os
import re, unicodedata
import tg
import gettext
import math
import inspect


class NoDefault(object):
    """A dummy value used for parameters with no default."""


def slugify(value, type, models):
    if isinstance(value, dict):
        for k, v in value.iteritems():
            key = k
            value = v
        counter = models.Product.query.find({'name.%s' % key: value, 'type': type}).count()
    else:
        counter = models.Product.query.find({'name.%s' % tg.config.lang: value, 'type': type}).count()

    value = type + '-' + value
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    value = re.sub('[-\s]+', '-', value)
    value = value + '-' + str(counter)
    return value


def slugify_category(value, models):
    if isinstance(value, dict):
        for k, v in value.iteritems():
            key = k
            value = v
        counter = models.Category.query.find({'name.%s' % key: value}).count()
    else:
        counter = models.Category.query.find({'name.%s' % tg.config.lang: value}).count()

    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    value = re.sub('[-\s]+', '-', value)
    if counter != 0:
        value += '-' + str(counter)
    return value


def short_lang(languages_list):
    try:
        return languages_list[0].split("_")[0]
    except (IndexError, TypeError):
        return tg.config.lang


def internationalise(value):
    if isinstance(value, dict):
        return value
    return {tg.config.lang: value}


def preferred_language():
    return short_lang(tg.i18n.get_lang(all=False))


class with_currency(object):
    @staticmethod
    def float2cur(n):
        return int(round(n*100.0))

    @staticmethod
    def cur2float(n):
        return math.floor(float(n))/100.0

    def __init__(self, *args):
        self.currencies = args

    def __call__(self, f):
        def _decorated(*args, **kwargs):
            named_params = inspect.getcallargs(f, *args, **kwargs)
            for cur in self.currencies:
                value = named_params[cur]
                named_params[cur] = self.float2cur(value)
            return self.cur2float(f(**named_params))
        return _decorated


@with_currency('price')
def apply_vat(price, vat):
    return price*vat


@with_currency('total', 'discount')
def apply_discount(total, discount):
    return total - discount


def apply_percentage_discount(total, percentage):
    discount = get_percentage_discount(total, percentage)
    return apply_discount(total, discount)


@with_currency('total')
def get_percentage_discount(total, percentage):
    return total * (percentage / 100.0)
