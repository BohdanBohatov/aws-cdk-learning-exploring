import yaml
import os
from typing import Dict, Any

class Configuration:
    def __init__(self, environment: str):
        self.environment = environment
        self.config = self._load_config()

    def _load_config(self) -> dict:
        config_path = os.path.join(
            os.path.dirname(__file__),
            f'../configs/{self.environment}.yaml'
        )
        with open(config_path, 'r') as config_file:
            return yaml.safe_load(config_file)

    def get_config(self) -> dict:
        return self.config

    def get_vpc_config(self) -> dict:
        return self.config.get('vpc', {})

    def get_tags_config(self) -> Dict[str, str]:
        return self.config.get('tags', {})

    def get_database_config(self) -> Dict[str, str]:
        return self.config.get('database', {})