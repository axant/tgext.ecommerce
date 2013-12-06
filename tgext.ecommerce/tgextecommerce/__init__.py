# -*- coding: utf-8 -*-
"""The tgext.ecommerce package"""
from lib.shop import Shop

def plugme(app_config, options):
    if not hasattr(app_config, 'DBSession'):
        app_config.DBSession = app_config.package.model.DBSession

    print app_config['tg.app_globals']
    return dict(appid='shop', global_helpers=False, plug_bootstrap=False)