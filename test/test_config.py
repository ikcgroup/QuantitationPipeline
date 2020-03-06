#! /usr/bin/env python3

import unittest

from quantify_proteins import ConfigError, QuantifyConfig


TEST_CONFIG_FILE = "test_config.json"


class QuantifyConfigTests(unittest.TestCase):
    def test_validate(self):
        try:
            QuantifyConfig(TEST_CONFIG_FILE).validate()
        except ConfigError as e:
            self.fail(e.message)


if __name__ == "__main__":
    unittest.main()
