from flask import render_template, flash, request
from flask_table import Table, Col, BoolNaCol, ButtonCol
from flask_table.columns import element
from app.settings import bpr
from app import sensor_simulator_handler
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
                 form_fields=None,  # Added this argument
                 **kwargs):
        super().__init__(name,
                         endpoint,
                         attr, attr_list,
                         url_kwargs,
                         button_attrs,
                         form_attrs,
                         form_hidden_fields=None,
                         **kwargs)
        self.form_fields = form_fields or {}  # Added this argument

    # Overriding: fields replace hidden fields
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
                ''.join(form_fields_elements),
                button
            ],
            escape_content=False,
        )


class BoolSettingsTable(Table):
    name = Col('Name', th_html_attrs={"style": "width:20%"})
    enabled = BoolNaCol('Enabled', th_html_attrs={"style": "width:20%"})
    change_value = ButtonCol(
        'Toggle function', 'settings.show_settings',
        url_kwargs=dict(name='name', enabled='enabled'),
        # this ends up in request.values as an identifier
        th_html_attrs={"style": "width:20%"},
        button_attrs={"name": "form_change"})


class FieldSettingsTable(Table):
    name = Col('Name', th_html_attrs={"style": "width:20%"})
    value = Col('Value', th_html_attrs={"style": "width:20%"})
    change_value = FieldButtonCol(
        'Update value', 'settings.show_settings',
        url_kwargs=dict(name='name'),
        # this ends up in request.values as an identifier
        button_attrs={"name": "form_change"},
        th_html_attrs={"style": "width:20%"},
        form_fields={"input_field": ""})


class BoolSetting(object):
    def __init__(self, name, enabled) -> None:
        self.name = name
        self.enabled = enabled


class FieldSetting(object):
    def __init__(self, name, value) -> None:
        self.name = name
        self.value = value


@bpr.route('', methods=['POST', 'GET'])
def show_settings():
    with open("./appsettings.json") as f:
        settings_data = json.load(f)
        f.close()
    if request.method == 'POST':
        if 'enabled' not in request.args:  # field value updated
            raw_value = request.form.get('input_field')
            if not str.isdigit(raw_value):
                flash("Please enter a number.")
            else:
                value = int(request.form.get('input_field'))
                if request.args['name'] == "update interval [s]" and value < 5:
                    flash("Please enter an update interval of > 5 s.")
                else:
                    settings_data[request.args['name']] = value
        else:  # toggle bool
            settings_data[request.args['name']] = False \
                if request.args['enabled'] == "True" else True
        with open("./appsettings.json", 'w', encoding='utf-8') as f:
            json.dump(settings_data, f, indent=4)
            f.close()
        sensor_simulator_handler.update_simulated_devices()
    bool_settings = []
    field_settings = []
    for key in settings_data.keys():
        is_bool = isinstance(settings_data[key], bool)
        if is_bool:
            bool_settings.append(BoolSetting(name=key,
                                             enabled=settings_data[key]))
        else:
            field_settings.append(FieldSetting(name=key,
                                               value=settings_data[key]))
    bool_settings_table = BoolSettingsTable(bool_settings)
    field_settings_table = FieldSettingsTable(field_settings)
    bool_settings_table.table_id = "bool_settings"
    bool_settings_table.classes = ["table", "table-striped"]
    field_settings_table.table_id = "field_settings"
    field_settings_table.classes = ["table", "table-striped"]
    return render_template('settings/settings.html',
                           bool_settings=bool_settings_table,
                           field_settings=field_settings_table)
