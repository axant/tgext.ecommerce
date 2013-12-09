# -*- coding: utf-8 -*-
"""The tgext.ecommerce package"""
from lib.shop import ShopManager

def plugme(app_config, options):
    if not hasattr(app_config, 'DBSession'):
        app_config.DBSession = app_config.package.model.DBSession

    return dict(appid='shop', global_helpers=False, plug_bootstrap=False)