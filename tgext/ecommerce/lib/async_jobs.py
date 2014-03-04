from contextlib import contextmanager
from itertools import chain
import logging
from tgext.ecommerce.model import DBSession, Cart, Product, Setting


@contextmanager
def cleanup_session(session):
    yield
    session.flush_all()
    session.close_all()


def clean_expired_carts():
    with cleanup_session(DBSession):
        expired_carts = Cart.expired_carts().all()
        expired_items = chain(*[c.items.iteritems() for c in expired_carts])
        for sku, item in expired_items:
            DBSession.update(Product, {'configurations.sku': sku},
                             {'$inc': {'configurations.$.qty': item['qty']}})
        [c.delete() for c in expired_carts]


def lock_carts():
    print 'Locking carts...'
    with cleanup_session(DBSession):
        locked = Setting.query.find({'setting': 'cart_locked'}).first()
        if locked is None:
            locked = Setting(setting='cart_locked')
        locked.value = True
    with cleanup_session(DBSession):
        all_carts = Cart.query.find().all()
        all_items = chain(*[c.items.iteritems() for c in all_carts])
        for sku, item in all_items:
            DBSession.update(Product, {'configurations.sku': sku},
                             {'$inc': {'configurations.$.qty': item['qty']}})
        [c.delete() for c in all_carts]


def unlock_carts():
    with cleanup_session(DBSession):
        locked = Setting.query.find({'setting': 'cart_locked'}).first()
        locked.value = False
    print 'Carts unlocked'