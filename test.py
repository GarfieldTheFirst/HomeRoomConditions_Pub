import unittest
import time
import json

from datetime import datetime, timedelta
from config import TestConfig
from sqlalchemy_utils import create_database, database_exists

from app.db_handler.db_handler import store_new_device, \
    get_stored_device, set_stored_devices_recording_setting, \
    get_data_for_recording_devices
from app.data_collector.data_collector_handler import DataCollectorHandler
from app.device_discovery_tool.device_discovery import \
    get_discovered_devices_list
from app.sensorsimulator.simulator_handler import SensorSimulatorHandler
from app import create_app, db

with open("./appsettings.json") as f:
    settings_data = json.load(f)
    f.close()


class DataCollectorTest(unittest.TestCase):
    config_class = TestConfig

    def setUp(self) -> None:
        self.app = create_app(config_class=self.config_class)
        self.app_context = self.app.app_context()
        self.app_context.push()
        if not database_exists(db.engine.url):
            create_database(db.engine.url)
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()

    def test_simulation_recording_getting_data(self):
        sensor_simulator_handler = SensorSimulatorHandler()
        sensor_simulator_handler.update_simulated_devices()
        assert settings_data["simulated device enabled"]
        time.sleep(5)
        discovered_devices_list = get_discovered_devices_list()
        assert discovered_devices_list
        data_collector_handler = DataCollectorHandler(db=db, app=self.app)
        for discovered_device in discovered_devices_list:
            store_new_device(name=discovered_device['name'],
                             ip=discovered_device['ip'],
                             connected=False)
            stored_device = get_stored_device(name=discovered_device['name'])
            set_stored_devices_recording_setting(
                stored_devices=[stored_device],
                value=True)
        data_collector_handler.update_devices_to_be_monitored()
        attempts = 0
        devices_data_dict = None
        data_arrived = False
        while attempts < 10 and not data_arrived:
            start_date = datetime.utcnow() - timedelta(hours=1)
            hours_to_monitor = 1
            sample_period_hours = hours_to_monitor // \
                settings_data["number of points to show"]
            devices_data_dict, device_list = get_data_for_recording_devices(
                sample_period_hours=sample_period_hours,
                retrieval_start_date=start_date)
            data_arrived = True if devices_data_dict["GArduinoSimulation"] \
                else False
            time.sleep(settings_data["update interval [s]"])
            attempts += 1
        assert data_arrived
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
        assert "GArduinoSimulation" in devices_data_dict.keys()
        assert 18 <= \
            data_for_template_dict["GArduinoSimulation"]['temperatures'][0] \
            <= 28
        assert 30 <= \
            data_for_template_dict["GArduinoSimulation"]['humidities'][0]\
            <= 60
        assert data_for_template_dict["GArduinoSimulation"]['movements'][0] \
            in [0, 1]
        settings_data["simulated device enabled"] = False
        sensor_simulator_handler.update_simulated_devices()
        set_stored_devices_recording_setting(
            stored_devices=[stored_device],
            value=False)
        data_collector_handler.update_devices_to_be_monitored()
