# coding=utf-8
from __future__ import unicode_literals
from datetime import date, datetime
from itertools import groupby
from bson import ObjectId
from tg import TGController, expose, validate, lurl, redirect, request, tmpl_context, config, flash, predicates
from tg.i18n import lazy_ugettext as l_
import tw2.core as twc
import tw2.forms as twf
from tw2.forms.widgets import BaseLayout
from tgext.ecommerce.lib import get_edit_order_form
from tgext.ecommerce.model import Order


FILTER_FIELDS = [('status_changes.changed_at', l_('date')), ('status', l_('status')), ('user', l_('user'))]


class MaybeDateValidator(twc.Validator):
    date_format = '%d/%m/%Y'

    def _convert_to_python(self, value, state=None):
        if value['field'] == 'status_changes.changed_at':
            try:
                value['filt'] = datetime.strptime(value['filt'], self.date_format)
            except:
                raise twc.ValidationError(l_('Date format must be dd/mm/yyyy'))
        return value

    def _convert_from_python(self, value, state=None):
        if value['field'] == 'status_changes.changed_at':
            value['filt'] = value['filt'].strftime(self.date_format)
        return value


class OrderFilterForm(twf.Form):
    submit = None
    buttons = [twf.Button(value=l_('RESET'), css_class='btn btn-default',
                          attrs={'data-url': lurl('/shop/manage/orders'), 'onclick': 'resetClick(this)'})]
    css_class = 'form-inline'

    class child(BaseLayout):
        inline_engine_name = 'genshi'
        template = """
<div xmlns:py="http://genshi.edgewall.org/" style="display: inline-block">
    <py:for each="c in w.children_hidden">
        ${c.display()}
    </py:for>
    <div>
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
        filt = twf.TextField(label=None, validator=twc.Validator(required=True), placeholder=l_('filter'),
                             css_class="form-control")
        submit = twf.SubmitButton(value=l_('FILTER'), css_class='btn btn-default')
        validator = MaybeDateValidator()


class ManageController(TGController):
    allow_only = predicates.in_group('managers')
    def _before(self, *args, **kw):
        tmpl_context.manage_pages = True

    @expose('tgext.ecommerce.templates.orders')
    def orders(self, **kw):
        orders = Order.query.find().sort('creation_date', -1).limit(250)
        grouped_orders = groupby(orders, lambda o: o.creation_date.strftime('%d/%m/%Y'))
        all_the_vats = Order.all_the_vats()
        return dict(orders=grouped_orders, form=OrderFilterForm, value=kw, action=self.mount_point+'/submit_orders',
                    bill_issue=self.mount_point+'/bill_issue/%s', notes=self.mount_point+'/notes/%s',
                    message=self.mount_point+'/message/%s',
                    edit=self.mount_point+'/edit?order_id=%s', all_the_vats=all_the_vats)

    @expose('tgext.ecommerce.templates.orders')
    @validate(OrderFilterForm, error_handler=orders)
    def submit_orders(self, **kw):
        if kw['field'] == 'user':
            orders = Order.query.find({kw['field']: {'$regex': kw['filt'], '$options': 'i'}})
        elif kw['field'] == 'status_changes.changed_at':
            date_ = kw['filt']
            day_start = datetime(date_.year, date_.month, date_.day)
            day_end = datetime(date_.year, date_.month, date_.day, 23, 59, 59)
            orders = Order.query.find({kw['field']: {'$gte': day_start, '$lte': day_end}})
        else:
            orders = Order.query.find({kw['field']: kw['filt']})
        orders = orders.sort('status_changes.changed_at', -1).limit(250)
        grouped_orders = groupby(orders, lambda o: o.status_changes[-1].changed_at.strftime('%d/%m/%Y'))
        all_the_vats = Order.all_the_vats()
        return dict(orders=grouped_orders, form=OrderFilterForm, value=kw, action=self.mount_point+'/submit_orders',
                    bill_issue=self.mount_point+'/bill_issue/%s', notes=self.mount_point+'/notes/%s',
                    all_the_vats=all_the_vats)

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

    @expose('tgext.ecommerce.templates.notes')
    def notes(self, order_id, **kw):
        order = Order.query.get(_id=ObjectId(order_id))
        return dict(notes=order.notes)

    @expose('tgext.ecommerce.templates.message')
    def message(self, order_id, **kw):
        order = Order.query.get(_id=ObjectId(order_id))
        return dict(message=order.message)

    @expose('tgext.ecommerce.templates.edit_order')
    def edit(self, **kw):
        order = Order.query.get(_id=ObjectId(kw.get('order_id', kw.get('_id'))))
        if order.status == 'shipped':
            flash(l_('Is not possible to edit a shipped Order'), 'error')
            return redirect(self.mount_point + '/orders')
        return dict(form=get_edit_order_form(), value=order)

    @expose()
    @validate(get_edit_order_form(), error_handler=edit)
    def save(self, **kw):
        order = Order.query.get(_id=ObjectId(kw['_id']))
        if kw.get('bill'):
            for k, v in kw.get('bill_info').iteritems():
                setattr(order.bill_info, k, v)
        for k, v in kw.get('shipment_info').iteritems():
            setattr(order.shipment_info, k, v)
        for k, v in kw.get('details').iteritems():
            setattr(order.details, k, v)
        flash(l_('Order successfully edited'))
        return redirect(self.mount_point + '/orders')
