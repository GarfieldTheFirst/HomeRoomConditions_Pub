# from sshtunnel import SSHTunnelForwarder
# from config import TestConfig, DevelConfigMYSQL
# from app.datacollector.datasender import SSHFileSender

import json
import unittest
import time

from config import TestConfig

from app.models.roomdata import Roomdata
from sqlalchemy_utils import create_database, database_exists


from app.data_collector.web_api import API
from app.data_collector.data_collector import DataCollector
from app.device_discovery_tool.device_discovery import get_devices
from app import create_app, db


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

    def test_webapi(self):
        connection = API(arduino_base_url=self.config_class.OFFICE_ARDUINO_URL)
        data = connection.get_all_data()
        temperature = data['variables']['temperature']
        humidity = data['variables']['humidity']
        movementDetected = data['variables']['movementDetected']
        name = data['name']
        assert temperature
        assert humidity
        assert movementDetected is not None
        assert name

    def test_storage(self):
        office_data_collector = DataCollector(
            app=self.app,
            db=db,
            arduino_base_url=self.config_class.OFFICE_ARDUINO_URL,
            collection_interval=1,
            simulated=True)
        office_data_collector.start()
        time.sleep(5)
        office_data_collector.stop_event.set()
        data = list(Roomdata.query.all())
        assert data
        if data:
            data = list(filter(lambda x: x, data))  # remove empty lines
            for item in data:
                print(item.date)
                print(item.humidity)
                print(item.temperature)
                print(item.movement_detection)


class NetworkScanTest(unittest.TestCase):
    def test_if_scan_works(self):
        results = get_devices()
        print(results)
        assert results  # Arduinos need to be in the network


class AppSettingsTest(unittest.TestCase):
    def test_json_file_loading(self):
        with open("./appsettings.json") as f:
            data = json.load(f)
            f.close()
        assert data
        updated_data = data
        updated_data["devices_to_monitor"].update(
            {"test_device": "0.0.0.0"})
        with open("./appsettings.json", 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=4)
            f.close()
        f = open("./appsettings.json",)
        newly_read_data = json.load(f)
        assert newly_read_data == updated_data
        with open("./appsettings.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.close()
