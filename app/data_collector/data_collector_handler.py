from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.data_collector.data_collector import DataCollector
from app.db_handler.db_handler import get_stored_devices_to_be_monitored


class DataCollectorHandler():
    def __init__(self,
                 db: SQLAlchemy,
                 app: Flask = None):
        self.app = app
        self.db = db
        self.device_ip_list = None
        self.collector_pool = {}

    def update_devices_to_be_monitored(self):
        # initiate
        self.device_ip_list = self.get_device_ips_to_be_monitored()
        if len(self.collector_pool) == 0:
            for ip in self.device_ip_list:
                self.collector_pool.update(
                    {ip: DataCollector(app=self.app, db=self.db, ip=ip)})
                self.collector_pool[ip].start()
        else:
            ips = list(self.collector_pool.keys())
            # remove ones that are not supposed to be monitored
            for ip in ips:
                if ip not in self.device_ip_list:
                    self.collector_pool[ip].stop_event.set()
                    self.collector_pool.pop(ip)
            # start the ones that are supposed to be there
            for ip in self.device_ip_list:
                if ip not in ips:
                    self.collector_pool.update(
                        {ip: DataCollector(
                            app=self.app, db=self.db, ip=ip)})
                    self.collector_pool[ip].start()

    def get_device_ips_to_be_monitored(self):
        with self.app.app_context():
            stored_devices_to_be_monitored = \
                get_stored_devices_to_be_monitored()
        device_ip_list = [device.ip
                          for device in stored_devices_to_be_monitored]
        return device_ip_list
