from tg import config
from tgext.ecommerce.lib.utils import preferred_language


def i_entity_value(entity, key):
    return entity.get(key).get(preferred_language(), entity.get(key).get(config.lang))

def format_price(price):
    return ('%0.3f' % price)[0:-1]