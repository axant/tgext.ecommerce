from tg import expose

@expose('tgextecommerce.templates.little_partial')
def something(name):
    return dict(name=name)