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
        expired_carts = models.Cart.expired_carts().all()
        expired_items = chain(*[c.items.iteritems() for c in expired_carts])
        for sku, item in expired_items:
            DBSession.update(models.Product, {'configurations.sku': sku},
                             {'$inc': {'configurations.$.qty': item['qty']}})
        [c.delete() for c in expired_carts]