# -*- coding: utf-8 -*-

import logging

from django import template
from django.core.urlresolvers import reverse
from django.forms import Form, ModelForm
from django.template import Variable
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

register = template.Library()


def split_args(args):
    #TODO hacer mejor y mover:
    #los parametros son posicionales
    # los opt returnan un diccionario
    tag = ''
    opts = []
    kwargs = {}
    tag = args[0]
    for arg in args[1:]:
        if '=' in arg:
            opt, value = arg.split('=')
            opt = str(opt)
            if value[0] == value[-1] and (value[0] == "'" or value[0] == '"'):
                kwargs[opt] = value[1:-1]
            elif value == 'True':
                kwargs[opt] = True
            elif value == 'False':
                kwargs[opt] = False
            else:
                kwargs[opt] = value
        else:
            opts.append(arg)
    return tag, opts, kwargs


class RenderFormNode(template.Node):

    def __init__(self, form, **kwargs):
        if not isinstance(form, (Form, ModelForm)):
            self.form = template.Variable(form)
        else:
            self.form = form
        self.placeholder = kwargs.get('placeholder', False)
        self.button_name = kwargs.get('button_name', _('Send'))
        self.dijit_tooltip = kwargs.get('dijit_tooltip', False)
        self.action_name = kwargs.get('action_name', None)
        self.action_url = kwargs.get('action_url', '/')
        self.template_form = kwargs.get('template_form', 'form/form.html')
        self.template_field = kwargs.get('template_field', 'form/field.html')
        self.only_fields = kwargs.get('only_fields', False)
        self.fieldset = kwargs.get('fieldset', None)
        self.mark_required = kwargs.get('mark_required', '')
        if self.action_name:
            self.action = reverse(self.action_name)
            self.action_id = self.action_name
        else:
            self.action = self.action_url
            self.action_id = '-'.join(self.action_url.split('/'))
        self.action_id = 'form-' + self.action_id
        self.form_id = kwargs.get('id', self.action_id)
        self.upload_files = kwargs.get('upload_files', False)

    def render(self, context):
        try:
            if isinstance(self.form, Variable):
                form = self.form.resolve(context)
            else:
                form = self.form
            if self.fieldset:
                self.fieldset = context[self.fieldset]
            c = {}
            c['form'] = form
            c['placeholder'] = self.placeholder
            c['button_name'] = self.button_name
            c['dijit_tooltip'] = self.dijit_tooltip
            c['only_fields'] = self.only_fields
            c['action'] = self.action
            c['form_id'] = self.form_id
            c['mark_required'] = self.mark_required
            #c['action_id'] = self.action_id
            if self.upload_files:
                c['upload'] = mark_safe('enctype="multipart/form-data"')
            else:
                c['upload'] = ''
            fields_string = ""
            if self.fieldset:
                for fieldset_group in self.fieldset:
                    key, fields = fieldset_group
                    fields_rendered = ''
                    for field_name in fields:
                        field = None
                        for field in form:
                            if field_name == field.name:
                                d = {'field': field}
                                d.update(c)
                                fields_rendered += render_to_string(self.template_field, d, context_instance=context)
                                break
                    fields_string += '<h3>%s</h3><div class="block-fields">%s</div>' % (key, fields_rendered)
            else:
                for field in form:
                    d = {'field':field}
                    d.update(c)
                    fields_string += render_to_string(self.template_field, d, context_instance=context)
            c['fields'] = mark_safe(fields_string)
            return mark_safe(render_to_string(self.template_form, c, context_instance=context))
        except template.VariableDoesNotExist:
            return ''


@register.tag
def render_form(parser, token):
    args = token.split_contents()
    tag, opts, kwargs = split_args(args)

    return RenderFormNode(*opts, **kwargs)


@register.simple_tag()
def render_with_placeholder(field):
    res = unicode(field)
    pos = res.find('>')

    try:
        label = field.label._proxy____args[0]
    except:
        label = field.label

    return res[:pos] + u' placeholder="%s" ' % label + res[pos:]
