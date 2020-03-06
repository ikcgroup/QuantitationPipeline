#! /usr/bin/env python3

import json
import os
from typing import List

from .fdr import get_fdr_name
from .utilities import get_file_id


class ConfigError(Exception):
    """
    Exception indicating a problem with the config file.

    """
    pass


class QuantifyConfig:
    """
    """

    def __init__(self, config_file: str):
        """
        """
        with open(config_file) as fh:
            self._config = json.load(fh)

    @property
    def protein_summary_files(self) -> List[str]:
        """
        """
        return self._config["ProteinSummaryFiles"]

    @property
    def results_dir(self) -> str:
        """
        """
        return self._config["ResultsDirectory"]

    def validate(self):
        """

        Raises:
            ConfigError

        """
        errors: List[str] = []

        # 8-character ProteinSummary file name prefixes
        prefixes: List[str] = []
        for prot_summary in self.protein_summary_files:
            try:
                file_id = get_file_id(prot_summary)
            except IndexError:
                errors.append(f"Failed to generate file ID for {prot_summary} "
                              f"- name too short")
            else:
                prefixes.append(file_id)

            if os.path.exists(prot_summary):
                try:
                    fdr_path = get_fdr_name(prot_summary)
                except ValueError:
                    errors.append(f"ProteinSummary not found in name of "
                                  f"{prot_summary}")
                else:
                    if not os.path.exists(fdr_path):
                        errors.append(f"{fdr_path} NOT found")
            else:
                errors.append(f"{prot_summary} NOT found")

        # Check unique 8-character prefixes
        if len(set(prefixes)) != len(prefixes):
            errors.append(f"Duplicate ProteinSummary prefixes detected in "
                          f"{', '.join(prefixes)}")

        if errors:
            raise ConfigError("\n".join(errors))
