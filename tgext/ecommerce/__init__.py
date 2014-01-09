# -*- coding: utf-8 -*-
"""The tgext.ecommerce package"""
from lib.shop import ShopManager
from tg import hooks, config
from lib.utils import detect_preferred_language

def plugme(app_config, options):
    if not hasattr(app_config, 'DBSession'):
        app_config.DBSession = app_config.package.model.DBSession

    hooks.wrap_controller(autodetect_preferred_language)
    hooks.register('before_config', setup_global_objects)

    return dict(appid='shop', global_helpers=False, plug_bootstrap=False)


def setup_global_objects(app):
    config['tg.app_globals'].shop = ShopManager()
    return app


def autodetect_preferred_language(app_config, caller):
    def call(*args, **kw):
        detect_preferred_language()
        return caller(*args, **kw)
    return call
