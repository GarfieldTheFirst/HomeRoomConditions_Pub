from app.sensorsimulator.simulator import SensorSimulator
from app import settings_data


class SensorSimulatorHandler():
    def __init__(self) -> None:
        self.simulated_port_list = []
        self.simulator_pool = {}

    def update_simulated_devices(self):
        # initiate
        self.simulated_port_list = self.get_ports_of_simulated_devices()
        if len(self.simulator_pool) == 0:
            for port in self.simulated_port_list:
                if port:
                    self.simulator_pool.update(
                        {port: SensorSimulator(port=port)})
                    self.simulator_pool[port].start()
        else:
            ports = list(self.simulator_pool.keys())
            # remove ones that are not supposed to be monitored
            for port in ports:
                if port not in self.simulated_port_list:
                    self.simulator_pool[port].stop()
                    self.simulator_pool.pop(port)
            # start the ones that are supposed to be there
            for port in self.simulated_port_list:
                if port not in ports:
                    self.simulator_pool.update(
                        {port: SensorSimulator(port=port)})
                    self.simulator_pool[port].start()

    def get_ports_of_simulated_devices(self):
        simulated_port_list = [settings_data["simulated device port"] if
                               settings_data["simulated device enabled"] else
                               None]
        return simulated_port_list
