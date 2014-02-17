from datetime import date, datetime
from itertools import groupby
from bson import ObjectId
from tg import TGController, expose, validate, lurl, redirect, request
from tg.i18n import lazy_ugettext as l_
import tw2.core as twc
import tw2.forms as twf
from tw2.forms.widgets import BaseLayout
from tgext.ecommerce.model import Order


FILTER_FIELDS = [('status_changes.changed_at', l_('data')), ('status', l_('stato')), ('user', l_('utente'))]


class MaybeDateValidator(twc.Validator):
    date_format = '%d/%m/%Y'

    def _convert_to_python(self, value, state=None):
        if value['field'] == 'status_changes.changed_at':
            try:
                value['filt'] = datetime.strptime(value['filt'], self.date_format)
            except:
                raise twc.ValidationError(l_('La data deve essere nel formato dd/mm/yyyy'))
        return value

    def _convert_from_python(self, value, state=None):
        if value['field'] == 'status_changes.changed_at':
            value['filt'] = value['filt'].strftime(self.date_format)
        return value


class OrderFilterForm(twf.Form):
    css_class = 'form-inline'
    submit = None

    class child(BaseLayout):
        inline_engine_name = 'genshi'
        template = """
<div xmlns:py="http://genshi.edgewall.org/">
    <py:for each="c in w.children_hidden">
        ${c.display()}
    </py:for>
    <div class="form-inline">
        <div class="form-group">
            <span py:content="w.children.field.error_msg"/>
            ${w.children.field.display()}
        </div>
        <div class="form-group">
            <span py:content="w.children.filt.error_msg"/>
            ${w.children.filt.display()}
        </div>
        ${w.submit.display()}
    </div>
    <div class="error"><span class="error"><py:for each="error in w.rollup_errors"><p>${error}</p></py:for></span></div>
</div>
"""
        field = twf.SingleSelectField(label=None,
                                      validator=twc.OneOfValidator(values=[f[0] for f in FILTER_FIELDS], required=True),
                                      options=FILTER_FIELDS, css_class="form-control")
        filt = twf.TextField(label=None, validator=twc.Validator(required=True), placeholder=l_('filtro'),
                             css_class="form-control")
        submit = twf.SubmitButton(value=l_('FILTRA'), css_class='btn btn-default')
        validator = MaybeDateValidator()


class ManageController(TGController):
    @expose('tgext.ecommerce.templates.orders')
    def orders(self, **kw):
        orders = Order.query.find().sort('status_changes.changed_at', -1).limit(250)
        grouped_orders = groupby(orders, lambda o: o.status_changes[-1].changed_at.strftime('%d/%m/%Y'))
        return dict(orders=grouped_orders, form=OrderFilterForm, value=kw, action=self.mount_point+'/submit_orders',
                    bill_issue=self.mount_point+'/bill_issue/%s')

    @expose('tgext.ecommerce.templates.orders')
    @validate(OrderFilterForm, error_handler=orders)
    def submit_orders(self, **kw):
        if kw['field'] == 'user':
            orders = Order.query.find({kw['field']: {'$regex': kw['filt']}})
        elif kw['field'] == 'status_changes.changed_at':
            date_ = kw['filt']
            day_start = datetime(date_.year, date_.month, date_.day)
            day_end = datetime(date_.year, date_.month, date_.day, 23, 59, 59)
            orders = Order.query.find({kw['field']: {'$gte': day_start}, kw['field']: {'$lte': day_end}})
        else:
            orders = Order.query.find({kw['field']: kw['filt']})
        orders = orders.sort('status_changes.changed_at', -1).limit(250)
        grouped_orders = groupby(orders, lambda o: o.status_changes[-1].changed_at.strftime('%d/%m/%Y'))
        return dict(orders=grouped_orders, form=OrderFilterForm, value=kw, action=self.mount_point+'/submit_orders')

    @expose()
    def bill_issue(self, order_id):
        order = Order.query.get(_id=ObjectId(order_id))
        order.billed = True
        order.billed_by = request.identity['user'].user_id
        order.billed_date = datetime.utcnow()
        return redirect(self.mount_point + '/orders')

    @expose('tgext.ecommerce.templates.order_detail')
    def order_detail(self, order_id, **kw):
        order = Order.query.get(_id=ObjectId(order_id))
        return dict(order=order)
