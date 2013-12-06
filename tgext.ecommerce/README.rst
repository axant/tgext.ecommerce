About tgextecommerce
-------------------------

tgextecommerce is a Pluggable application for TurboGears2.

Installing
-------------------------------

tgextecommerce can be installed both from pypi or from bitbucket::

    easy_install tgextecommerce

should just work for most of the users

Plugging tgextecommerce
----------------------------

In your application *config/app_cfg.py* import **plug**::

    from tgext.pluggable import plug

Then at the *end of the file* call plug with tgextecommerce::

    plug(base_config, 'tgextecommerce')

You will be able to access the registration process at
*http://localhost:8080/tgextecommerce*.

Available Hooks
----------------------

tgextecommerce makes available a some hooks which will be
called during some actions to alter the default
behavior of the appplications:

Exposed Partials
----------------------

tgextecommerce exposes a bunch of partials which can be used
to render pieces of the blogging system anywhere in your
application:

Exposed Templates
--------------------

The templates used by registration and that can be replaced with
*tgext.pluggable.replace_template* are:

