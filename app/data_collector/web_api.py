import requests
import json


class API():
    def __init__(self, arduino_base_url: 'str') -> None:
        self.base_url = arduino_base_url

    def get_variable(self, variable_name):
        try:
            url = self.base_url + "/" + variable_name + "?"
            variable = json.loads(requests.get(url=url).content)[variable_name]
            return variable
        except TimeoutError:
            raise

    def get_all_data(self):
        try:
            url = self.base_url
            all_data = json.loads(requests.get(url=url).content)
            return all_data
        except TimeoutError:
            raise
