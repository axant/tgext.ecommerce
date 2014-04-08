# -*- coding: utf-8 -*-
"""The tgext.ecommerce package"""
import tg
from tgscheduler.scheduler import scheduler
from lib.shop import ShopManager
from tg import hooks, config
from tgext.ecommerce.lib.payments.paypal import configure_paypal


def plugme(app_config, options):

    hooks.register('before_config', setup_global_objects)
    hooks.register('after_config', setup_clean_cart_scheduler)
    hooks.register('after_config', init_paypal)

    return dict(appid='shop', global_helpers=False, plug_bootstrap=False)


def setup_global_objects(app):
    config['tg.app_globals'].shop = ShopManager()
    return app


def setup_clean_cart_scheduler(app):
    from lib.async_jobs import clean_expired_carts
    if scheduler._scheduler_instance is None:
        scheduler.start_scheduler()
    scheduler.add_interval_task(clean_expired_carts, 60)
    return app


def init_paypal(app):
    configure_paypal(tg.config['paypal_mode'], tg.config['paypal_client_id'], tg.config['paypal_client_secret'])
    return app
