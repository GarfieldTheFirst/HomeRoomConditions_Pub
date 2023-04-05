from flask import render_template, flash, request
from flask_table import Table, Col, BoolCol, ButtonCol
from app.devices import bpr
from app.devices.forms import SubmitForm
from app.device_discovery_tool.device_discovery import \
    get_discovered_devices_list
from app import data_collector_handler
from app.db_handler.db_handler import get_all_stored_devices, \
    get_stored_device, set_stored_devices_recording_setting, \
    store_new_device, set_stored_devices_connected_setting, \
    delete_stored_devices


class DeviceTable(Table):
    name = Col('Device name')
    ip = Col('Device ip')
    connected = BoolCol('Connected')
    recording = BoolCol('Recording')
    record = ButtonCol('Toggle recording', 'devices.show_devices',
                       url_kwargs=dict(name='name', ip='ip'),
                       # this ends up in request.values as an identifier
                       button_attrs={"name": "form_record"})
    delete = ButtonCol('Delete', 'devices.show_devices',
                       url_kwargs=dict(name='name'),
                       button_attrs={"name": "form_delete"})


class Device(object):
    def __init__(self, name, ip, connected, recording) -> None:
        self.name = name
        self.ip = ip
        self.connected = connected
        self.recording = recording


@bpr.route('', methods=['GET', 'POST'])
def show_devices():
    stored_devices = get_all_stored_devices()
    stored_device_names = [stored_device.name
                           for stored_device in stored_devices]
    form_1 = SubmitForm(prefix="form_1")
    discovered_devices_list = []
    if request.method == "POST":
        if "form_1-submit" in request.values:
            discovered_devices_list = get_discovered_devices_list()
            flash("Scan complete")
            for discovered_device in discovered_devices_list:
                if discovered_device['name'] not in stored_device_names:
                    store_new_device(name=discovered_device['name'],
                                     ip=discovered_device['ip'],
                                     connected=False)
                else:
                    device_to_update = get_stored_device(
                        name=discovered_device['name'])
        elif "form_record" in request.values:
            devices = []
            device_name_to_add = request.args['name']
            recording_device_names = [stored_device.name
                                      for stored_device in stored_devices
                                      if stored_device.recording]
            device_to_update = get_stored_device(name=device_name_to_add)
            if device_name_to_add not in recording_device_names:
                recording = True
                flash("Now recording device: {}".format(device_name_to_add))
            else:
                recording = False
                flash("No longer recording device: {}".format(
                    device_name_to_add))
                set_stored_devices_connected_setting(
                    stored_devices=[device_to_update], value=False)
            set_stored_devices_recording_setting(
                stored_devices=[device_to_update], value=recording)
        elif "form_delete" in request.values:
            device_name_to_remove = request.args['name']
            device_to_delete = get_stored_device(name=device_name_to_remove)
            delete_stored_devices(stored_devices=[device_to_delete])
        data_collector_handler.update_devices_to_be_monitored()
        stored_devices = get_all_stored_devices()
    devices = []
    for stored_device in stored_devices:
        devices.append(Device(name=stored_device.name,
                              ip=stored_device.ip,
                              connected=stored_device.connected,
                              recording=stored_device.recording))
    table = DeviceTable(devices)
    table.table_id = "devices"
    table.classes = ["table", "table-striped", "left-align"]
    return render_template('devices/devices.html',
                           data=table,
                           form_1=form_1)
