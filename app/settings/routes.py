from flask import render_template, flash, request
from flask_table import Table, Col, BoolNaCol, ButtonCol
from flask_table.columns import element
from app.settings import bpr
from app import settings_data, sensor_simulator_handler
import json


class FieldButtonCol(ButtonCol):
    def __init__(self,
                 name,
                 endpoint,
                 attr=None,
                 attr_list=None,
                 url_kwargs=None,
                 button_attrs=None,
                 form_attrs=None,
                 form_hidden_fields=None,
                 form_fields=None,
                 **kwargs):
        super().__init__(name,
                         endpoint,
                         attr, attr_list,
                         url_kwargs,
                         button_attrs,
                         form_attrs,
                         form_hidden_fields,
                         **kwargs)
        self.form_fields = form_fields or {}

    def td_contents(self, item, attr_list):
        button_attrs = dict(self.button_attrs)
        button_attrs['type'] = 'submit'
        button = element(
            'button',
            attrs=button_attrs,
            content=self.text(item, attr_list),
        )
        form_attrs = dict(self.form_attrs)
        form_attrs.update(dict(
            method='post',
            action=self.url(item),
        ))
        form_hidden_fields_elements = [
            element(
                'input',
                attrs=dict(
                    type='hidden',
                    name=name,
                    value=value))
            for name, value in sorted(self.form_hidden_fields.items())]
        form_fields_elements = [
            element(
                'input',
                attrs=dict(
                    type='text',
                    name=name,
                    value=value))
            for name, value in sorted(self.form_fields.items())]
        return element(
            'form',
            attrs=form_attrs,
            content=[
                ''.join(form_hidden_fields_elements),
                ''.join(form_fields_elements),
                button
            ],
            escape_content=False,
        )


class SettingsTable(Table):
    name = Col('Name')
    enabled = BoolNaCol('Enabled')
    value = Col("Value", td_html_attrs={"value_item": ""})
    change_value = FieldButtonCol(
        'Update value or toggle function', 'settings.show_settings',
        url_kwargs=dict(name='name', enabled='enabled'),
        # this ends up in request.values as an identifier
        button_attrs={"name": "form_change"},
        form_attrs={"method": "POST"},
        form_fields={"input_field": ""})


class Setting(object):
    def __init__(self, name, enabled, value) -> None:
        self.name = name
        self.enabled = enabled
        self.value = value


@bpr.route('', methods=['POST', 'GET'])
def show_settings():
    if request.method == 'POST':
        if 'enabled' not in request.args:
            raw_value = request.form.get('input_field')
            if not str.isdigit(raw_value):
                flash("Please enter a number.")
            else:
                value = int(request.form.get('input_field'))
                if request.args['name'] == "update interval [s]" and value < 5:
                    flash("Please enter an update interval of > 5 s.")
                else:
                    settings_data[request.args['name']] = value
        else:
            settings_data[request.args['name']] = False \
                if request.args['enabled'] == "True" else True
        with open("./appsettings.json", 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, indent=4)
            f.close()
        sensor_simulator_handler.update_simulated_devices()
    settings = []
    for key in settings_data.keys():
        is_bool = isinstance(settings_data[key], bool)
        setting = Setting(name=key,
                          enabled=settings_data[key]
                          if is_bool
                          else None,
                          value=settings_data[key]
                          if not is_bool
                          else None)
        settings.append(setting)
    table = SettingsTable(settings)
    table.table_id = "settings"
    table.classes = ["table", "table-striped"]
    return render_template('settings/settings.html', data=table)


# def expand_settings_dict(settings_data):
#     settings_list = []
#     for key in settings_data.keys():
#         if settings_data[key] is dict:
#             setting = Setting(name=key,
#                               value=settings_data[key])
#         else:
#             setting = Setting(name=key,
#                               value=settings_data[key])
#             settings_list.append(setting)
# email_submit_form = SubmitForm()
# if request.method == "POST" and \
#         email_submit_form.is_submitted():
#     send_email(subject="Test",
#                 sender=current_app.config['ADMINS'][0],
#                 recipients=current_app.config['ADMINS'],
#                 text_body="Flask_test",
#                 html_body=None)
#     flash("Email has been sent.")
