# -*- coding: utf-8 -*-
from tg import config


def get_edit_order_form():
    ecommerce_config = config['_pluggable_ecommerce_config']
    edit_order_form = ecommerce_config.get('edit_order_form_instance')
    if not edit_order_form:
        form_path = ecommerce_config.get('edit_order_form', 'tgext.ecommerce.lib.forms.DefaultEditOrderForm')
        module, form_name = form_path.rsplit('.', 1)
        module = __import__(module, fromlist=form_name)
        form_class = getattr(module, form_name)
        edit_order_form = ecommerce_config['edit_order_form_instance'] = form_class()

    return edit_order_form