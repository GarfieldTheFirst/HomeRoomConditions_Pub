from app import settings_data
import time
import logging
from datetime import datetime
from threading import Thread, Event
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, flash
from app.data_collector.web_api import API
from app.db_handler.db_handler import get_stored_device, store_measured_data, \
    get_correct_hour_id_to_link_to_measured_data, \
    set_stored_devices_connected_setting


class DataCollector(Thread):
    collector_number = 0

    def __init__(self,
                 ip,
                 app: Flask,
                 db: SQLAlchemy) -> None:
        super(DataCollector, self).__init__(
            target=self.collect_arduino_edge_data,
            args=())
        self.db = db
        self.ip = ip
        self.app = app
        self.stop_event = Event()
        self.stop_event.clear()
        DataCollector.collector_number += 1

    def collect_arduino_edge_data(self):
        while not self.stop_event.is_set():
            get_iteration_start_time = time.time()
            try:
                time_now = datetime.utcnow()
                with self.app.app_context():
                    device = get_stored_device(ip=self.ip)
                    hour_id = get_correct_hour_id_to_link_to_measured_data(
                        time_now=time_now)
                    data = API(arduino_base_url="http://" +
                               self.ip).get_all_data()
                    if not data:
                        continue
                    set_stored_devices_connected_setting(
                        stored_devices=[device], value=True)
                    store_measured_data(data=data,
                                        time_now=time_now,
                                        device_id=device.id,
                                        hour_id=hour_id)
            except TimeoutError as e:
                flash("Logger shutting down.")
                logging.info("No data recorded: {}".format(e))
                self.stop_event.set()
            except Exception as e:
                logging.info("No data recorded: {}".format(e))
                with self.app.app_context():
                    device = get_stored_device(ip=self.ip)
                    set_stored_devices_connected_setting(
                        stored_devices=[device], value=False)
            finally:
                collection_interval = settings_data["update interval [s]"]
                elapsed_time = time.time() - get_iteration_start_time
                if elapsed_time < collection_interval:
                    time.sleep(collection_interval - elapsed_time)
                else:
                    logging.info("Get iteration length not long enough,\
                        elapsed time: {} s".format(elapsed_time))
