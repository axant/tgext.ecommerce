About tgext.ecommerce
-------------------------

tgext.ecommerce is a Pluggable eCommerce Framework for TurboGears2.

Installing
-------------------------------

tgext.ecommerce can be installed both from pypi or from bitbucket::

    pip install tgext.ecommerce

should just work for most of the users

Plugging tgextecommerce
----------------------------

In your application *config/app_cfg.py* import **plug**::

    from tgext.pluggable import plug

Then at the *end of the file* call plug with tgext.ecommerce::

    plug(base_config, 'tgext.ecommerce')

You will be able to access tgext.ecommerge functions as ``tg.app_globals.shop``
