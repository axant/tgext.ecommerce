# -*- coding: utf-8 -*-
"""The tgext.ecommerce package"""
import base64

import tg
from tgscheduler.scheduler import scheduler
from .lib.shop import ShopManager
from tg import hooks, config
from tgext.ecommerce.lib.payments.paypal import configure_paypal


def plugme(app_config, options):
    try:
        # TG 2.3
        app_config['_pluggable_ecommerce_config'] = options
        hooks.register('before_config', setup_global_objects)
        hooks.register('after_config', setup_clean_cart_scheduler)
        hooks.register('after_config', init_payments)
    except TypeError:
        # TG 2.4
        app_config.update_blueprint({
            '_pluggable_ecommerce_config': options
        })
        hooks.register('before_wsgi_middlewares', setup_global_objects)
        hooks.register('after_wsgi_middlewares', setup_clean_cart_scheduler)
        hooks.register('after_wsgi_middlewares', init_payments)

    return dict(appid='shop', global_helpers=True, plug_bootstrap=False)


def setup_global_objects(app):
    config['tg.app_globals'].shop = ShopManager()
    return app


def setup_clean_cart_scheduler(app):
    from .lib.async_jobs import clean_expired_carts
    if scheduler._scheduler_instance is None:
        scheduler.start_scheduler()
    scheduler.add_interval_task(clean_expired_carts, 60)
    return app


def init_payments(app):
    if config['sage_integrationKey'] is not None:
        config['sage_header'] = "Basic " \
            + str(base64.b64encode(
                bytes(config['sage_integrationKey'] + ":" + config["sage_integrationPassword"], 'utf-8')
            ))
    if config['paypal_mode'] is not None:
        configure_paypal(config['paypal_mode'], config['paypal_client_id'], config['paypal_client_secret'])
    return app
