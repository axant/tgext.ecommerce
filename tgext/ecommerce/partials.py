from tg import expose

@expose('tgext.ecommerce.templates.little_partial')
def something(name):
    return dict(name=name)