import yaml
import os


class Config:
    def __init__(self, config_file: str):
        self._config = self._load_config(self._resolve_path(config_file))

    def _load_config(self, config_file: str):
        with open(config_file, 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    def _resolve_path(self, path):
        return path if path[0] == '/' else os.path.join(os.path.dirname(os.path.realpath(__file__)), path)

    def _get_property(self, property_name: str):
        return self._config.get(property_name)

    @property
    def mqtt_host(self):
        return self._get_property('mqtt_host')

    @property
    def mqtt_port(self):
        return self._get_property('mqtt_port')

    @property
    def mqtt_username(self):
        return self._get_property('mqtt_username')

    @property
    def mqtt_password(self):
        return self._get_property('mqtt_password')

    @property
    def hubitat_host(self):
        return self._get_property('hubitat_host')

    @property
    def hubitat_maker_token(self):
        return self._get_property('hubitat_maker_token')

    @property
    def hubitat_maker_app_id(self):
        return self._get_property('hubitat_maker_app_id')


config = Config('../../config/config.yaml')
