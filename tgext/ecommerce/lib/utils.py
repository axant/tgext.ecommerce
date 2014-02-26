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


def detect_preferred_language():
    translator = tg.translator._current_obj()
    try:
        return translator.preferred_language
    except AttributeError:
        conf = tg.config._current_obj()

        try:
            localedir = conf['localedir']
        except KeyError: #pragma: no cover
            localedir = os.path.join(conf['paths']['root'], 'i18n')

        try:
            mos = gettext.find(conf['package'].__name__, localedir, languages=getattr(translator, 'tg_lang', ['en']), all=True)
        except IOError as ioe:
            translator.preferred_language = conf['lang']
            return translator.preferred_language
        langs = []
        for i, mo in enumerate(mos):
            path, lang = os.path.split(os.path.split(os.path.dirname(mo))[0])
            langs.append(lang)
            if i == 0:
                translator.preferred_language = lang

        translator.supported_langs = langs
        return lang

