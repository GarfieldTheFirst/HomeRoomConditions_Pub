from flask import Blueprint, jsonify, request, render_template, flash
from datetime import datetime, timedelta
from app.forms import FilteringForm
from app.db_handler.db_handler import get_data_for_recording_devices
from app import settings_data


views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@views.route('/dashboard', methods=['GET', 'POST'])
def home():
    form_1 = FilteringForm(prefix="form_1")
    # By default (GET), get the data for the last hour
    start_date = datetime.utcnow() - timedelta(hours=1)
    if request.method == 'POST':
        if form_1.validate_on_submit():
            entered_start_date = form_1.start_date.data
            start_date = entered_start_date + \
                timedelta(hours=int(form_1.timezone_offset.data))
        else:
            flash("Incompete form data submitted!")
    start_date_to_send = start_date.strftime('%Y-%m-%dT%H:%M') + 'Z'
    sample_period_hours = (datetime.utcnow() - start_date) \
        // timedelta(hours=1) // settings_data["number of points to show"]
    data_for_template_dict = get_data_dict(start_date=start_date)
    return render_template("dashboard.html",
                           form_1=form_1,
                           start_date=start_date_to_send,
                           sample_period_hours=sample_period_hours,
                           data_for_template_dict=data_for_template_dict)


@views.route('/get_data', methods=['GET'])
def get_data():
    data_for_template_dict = get_data_dict(
        datetime.utcnow() - timedelta(hours=1))
    return jsonify(data_for_template_dict)


def get_data_dict(start_date):
    hours_to_monitor = (datetime.utcnow() - start_date) // timedelta(hours=1)
    sample_period_hours = hours_to_monitor // \
        settings_data["number of points to show"]
    devices_data_dict, device_list = get_data_for_recording_devices(
        sample_period_hours=sample_period_hours,
        start_date=start_date)
    data_for_template_dict = {}
    if devices_data_dict:
        for device in device_list:
            # remove empty lines
            devices_data_dict[device.name] = \
                list(filter(lambda x: x, devices_data_dict[device.name]))
            data_for_template_dict \
                .update({device.name: {
                    'labels':
                    [str(row.date) + 'Z'
                     for row in devices_data_dict[device.name]],
                    # Z indicates utc
                    'temperatures':
                    [row.temperature
                     for row in devices_data_dict[device.name]],
                    'humidities':
                    [row.humidity
                     for row in devices_data_dict[device.name]],
                    'movements':
                    [row.movement_detection
                     for row in devices_data_dict[device.name]]}})
    return data_for_template_dict
