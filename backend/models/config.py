import os
import yaml
from pathlib import Path


class Config:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._load_config()

    def _load_config(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                'config.yaml'
            )

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

    @property
    def train(self):
        return self._config.get('train', {})

    @property
    def loss(self):
        return self._config.get('loss', {})

    @property
    def inference(self):
        return self._config.get('inference', {})

    @property
    def wandb(self):
        return self._config.get('wandb', {})

    def get(self, key, default=None):
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value


config = Config()
