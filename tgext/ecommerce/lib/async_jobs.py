from contextlib import contextmanager
from itertools import chain
from tgext.ecommerce.model import DBSession, models


@contextmanager
def cleanup_session(session):
    yield
    session.flush_all()
    session.close_all()


def clean_expired_carts():
    with cleanup_session(DBSession):
        expired_carts = models.Cart.expired_carts()
        expired_items = chain(*[c.items.iteritems() for c in expired_carts])
        for item, qty in expired_items:
            DBSession.update(models.Product, {'configurations.sku': item},
                             {'$inc': {'configurations.$.qty': qty}})
        [c.delete() for c in expired_carts]