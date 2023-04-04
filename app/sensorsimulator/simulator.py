from flask import Flask
from flask_restful import Resource, Api
from random import Random
from multiprocessing import Process
import waitress


class SimulatedRoomData(Resource):
    def get(self):
        temperature = Random().randint(18, 28)
        humidity = Random().randint(30, 60)
        movement_detection = Random().choice(seq=[0, 1])
        return {"variables": {"temperature": temperature,
                              "humidity": humidity,
                              "movementDetected": movement_detection},
                "id": "999",
                "name": "GArduino-simulation",
                "hardware": "arduino",
                "connected": 1}


class SensorSimulator(Process):
    def __init__(self, port) -> None:
        self.app_sim = Flask("SensorSimulator")
        self.api = Api(self.app_sim)
        self.api.add_resource(SimulatedRoomData, '/')
        self.port = port
        super().__init__(target=self.run_server, args=())

    def run_server(self):
        waitress.serve(app=self.app_sim,
                       port=self.port)

    def stop(self):
        self.terminate()
