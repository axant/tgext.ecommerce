from contextlib import contextmanager
from datetime import datetime, timedelta
from itertools import chain
import logging
import os
from ming.odm import mapper
from pymongo.errors import DuplicateKeyError
from tgext.ecommerce.model import DBSession, Cart, Product, Setting

log = logging.getLogger('tgext.ecommerce')

@contextmanager
def cleanup_session(session):
    yield
    session.flush_all()
    session.close_all()


def clean_expired_cart(expired_cart):
    log.warn('Expiring Cart %s for user %s', expired_cart._id, expired_cart.user_id)

    for sku, item in expired_cart.items.iteritems():
        DBSession.update(Product, {'configurations.sku': sku},
                         {'$inc': {'configurations.$.qty': item['qty']}})

    expired_cart.delete()


def clean_expired_carts(clear_all=False):
    with cleanup_session(DBSession):
        if clear_all:
            expired_carts = Cart.query.find().all()
            for c in expired_carts:
                clean_expired_cart(c)
        else:
            now = datetime.utcnow()
            shifted_expire = now + timedelta(minutes=5)
            while True:
                expired_cart = Cart.query.find_and_modify(query={'expires_at': {'$lte': now}},
                                                          update={'$set': {'expires_at': shifted_expire}})
                if expired_cart is None:
                    break

                clean_expired_cart(expired_cart)


def cart_locked_by_me():
    locked_by_me = Setting.query.find({'setting': 'cart_locked', 'value': os.getpid()}).first()
    return locked_by_me is not None


def lock_carts():
    settings_collection = mapper(Setting).collection

    # Ensure there is the lock row
    try:
        DBSession.impl.insert(settings_collection({'setting': 'cart_locked', 'value': 0}))
    except DuplicateKeyError:
        pass

    # Try to get the lock
    mypid = os.getpid()
    locked = DBSession.impl.update_partial(settings_collection,
                                           {'setting': 'cart_locked',
                                            'value': 0},
                                           {'$set': {'value': mypid}})

    if locked.get('updatedExisting', False):
        log.warn('Cart Locked by %s...' % mypid)
        clean_expired_carts(clear_all=True)
    else:
        log.warn('Cart already locked!')


def unlock_carts():
    mypid = os.getpid()
    settings_collection = mapper(Setting).collection
    locked = DBSession.impl.update_partial(settings_collection,
                                           {'setting': 'cart_locked',
                                            'value': mypid},
                                           {'$set': {'value': 0}})

    if locked.get('updatedExisting', False):
        log.warn('Cart Unlocked by %s...' % mypid)