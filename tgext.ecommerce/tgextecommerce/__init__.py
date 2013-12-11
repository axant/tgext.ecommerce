# -*- coding: utf-8 -*-
"""The tgext.ecommerce package"""
from lib.shop import ShopManager
from tg import hooks, config


def plugme(app_config, options):
    if not hasattr(app_config, 'DBSession'):
        app_config.DBSession = app_config.package.model.DBSession

    hooks.register('before_config', setup_global_objects)

    return dict(appid='shop', global_helpers=False, plug_bootstrap=False)


def setup_global_objects(app):
    config['tg.app_globals'].shop = ShopManager()
    return app