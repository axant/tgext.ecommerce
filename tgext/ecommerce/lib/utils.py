import os
import re, unicodedata
import tg
import gettext


class NoDefault(object):
    """A dummy value used for parameters with no default."""


def slugify(value, type, models):
    counter = models.Product.query.find({'name.%s' % tg.config.lang: value, 'type': type}).count()
    value = type + '-' + value
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    value = re.sub('[-\s]+', '-', value)
    value = value + '-' + str(counter)
    return value


def short_lang(languages_list):
    return languages_list[0].split("_")[0]


def internationalise(value):
    if isinstance(value, dict):
        return value
    return {tg.config.lang: value}


def preferred_language():
    return short_lang(tg.i18n.get_lang(all=False))
