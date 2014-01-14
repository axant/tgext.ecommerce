# -*- coding: utf-8 -*-
"""The tgext.ecommerce package"""
import tgscheduler
from lib.shop import ShopManager
from tg import hooks, config
from lib.utils import detect_preferred_language

def plugme(app_config, options):
    if not hasattr(app_config, 'DBSession'):
        app_config.DBSession = app_config.package.model.DBSession

    hooks.wrap_controller(autodetect_preferred_language)
    hooks.register('before_config', setup_global_objects)
    hooks.register('after_config', setup_clean_cart_scheduler)

    return dict(appid='shop', global_helpers=False, plug_bootstrap=False)


def setup_global_objects(app):
    config['tg.app_globals'].shop = ShopManager()
    return app


def autodetect_preferred_language(app_config, caller):
    def call(*args, **kw):
        detect_preferred_language()
        return caller(*args, **kw)
    return call


def setup_clean_cart_scheduler(app):
    from lib.async_jobs import clean_expired_carts
    tgscheduler.start_scheduler()
    tgscheduler.add_interval_task(clean_expired_carts, 60)
    return app