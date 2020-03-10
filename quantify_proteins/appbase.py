#! /usr/bin/env python3

import os

from .quantify_config import QuantifyConfig
from .utilities import dir_exists


class AppBase:
    """
    """
    def __init__(self, config_file: str):
        """
        """
        self.config = QuantifyConfig.from_file(config_file)

        if not dir_exists(self.config.results_dir):
            os.makedirs(self.config.results_dir)

    def validate_config(self):
        """
        Validates the configuration file to ensure that input is appropriate
        for use.

        Raises:
            ConfigError

        """
        self.config.validate()
