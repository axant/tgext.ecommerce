import re, unicodedata
import tg


def slugify(value, type, models):
    counter = models.Product.query.find({'name': value, 'type':type}).count()
    value = type + '-' + value
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    value = re.sub('[-\s]+', '-', value)
    value = value + '-' + str(counter)
    return value

def internationalise(value):
    if isinstance(value, dict):
        return value

    return {tg.config.lang: value}



