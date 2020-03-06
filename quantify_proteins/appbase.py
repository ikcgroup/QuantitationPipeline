#! /usr/bin/env python3

from .quantify_config import ConfigError, QuantifyConfig


class AppBase:
    """
    """
    def __init__(self, config_file: str):
        """
        """
        self._config = QuantifyConfig(config_file)

    def validate_config(self):
        """
        Validates the configuration file to ensure that input is appropriate
        for use.

        Raises:
            ConfigError

        """
        self._config.validate()
