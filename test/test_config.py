#! /usr/bin/env python3

import os
import unittest

from quantify_proteins import ConfigError, QuantifyConfig

from .test_common import TEST_CONFIG_DIR


TEST_CONFIG_FILE = os.path.join(TEST_CONFIG_DIR, "test_config.json")
EMPTY_CONFIG_FILE = os.path.join(TEST_CONFIG_DIR, "empty.json")


class QuantifyConfigTests(unittest.TestCase):
    def test_validate(self):
        try:
            QuantifyConfig.from_file(TEST_CONFIG_FILE).validate()
        except ConfigError as e:
            self.fail(e.message)

    # TODO: add tests for failed validation


if __name__ == "__main__":
    unittest.main()
