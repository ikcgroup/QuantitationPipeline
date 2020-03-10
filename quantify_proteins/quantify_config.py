#! /usr/bin/env python3

# This enables delayed evaluation of type hints, which is necessary for the
# classmethods defined below
from __future__ import annotations
import json
import os
from typing import Dict, List

from .fdr import get_fdr_name
from .utilities import get_file_id


ITRAQ_TAGS = {
    "113",
    "114",
    "115",
    "116",
    "117",
    "118",
    "119",
    "121"
}


class ConfigError(Exception):
    """
    Exception indicating a problem with the config file.

    """
    pass


def _validate_file_list(files: List[str]) -> List[str]:
    """
    Validates the given list of ProteinSummary/Peptide Summary files, in terms
    of file existence, existence of corresponding FDR files and prefix
    uniqueness.

    Args:
        files (list): A list of file paths.

    Returns:
        list: A list of errors identified in the configuration.

    """
    errors: List[str] = []

    # 8-character file name prefixes
    prefixes: List[str] = []
    for file_path in files:
        try:
            file_id = get_file_id(file_path)
        except IndexError:
            errors.append(f"Failed to generate file ID for {file_path} "
                          f"- name too short")
        else:
            prefixes.append(file_id)

        if os.path.exists(file_path):
            try:
                fdr_path = get_fdr_name(file_path)
            except ValueError as e:
                errors.append(e.message)
            else:
                if not os.path.exists(fdr_path):
                    errors.append(f"{fdr_path} NOT found")
        else:
            errors.append(f"{file_path} NOT found")

    # Check unique 8-character prefixes
    if len(set(prefixes)) != len(prefixes):
        errors.append(f"Duplicate id prefixes detected in "
                      f"{', '.join(prefixes)}")

    return errors


class QuantifyConfig:
    """
    A class to provide standardized access to the underlying JSON config.

    """
    def __init__(self, config_data: Dict):
        """
        Initializes the QuantifyConfig instance. In general, the class methods
        from_file and from_dict should be used, rather than accessing this
        constructor directly.

        Args:
            config_data (dict): A configuration dictionary.

        """
        self._config = config_data

    @classmethod
    def from_file(cls, config_file: str) -> QuantifyConfig:
        """
        Initializes the QuantifyConfig using a JSON input file.

        Args:
            config_file (str): The path to the JSON configuration file.

        Returns:
            QuantifyConfig

        """
        with open(config_file) as fh:
            data = json.load(fh)
        return cls(data)

    @classmethod
    def from_dict(cls, config_dict: Dict) -> QuantifyConfig:
        """
        Initializes the QuantifyConfig using a dictionary.

        Args:
            config_dict (dict): A dictionary with valid configuration options.

        Returns:
            QuantifyConfig

        """
        return cls(config_dict)

    @property
    def protein_summary_files(self) -> List[str]:
        """
        A list of ProteinSummary files to be processed.

        """
        return self._config.get("ProteinSummaryFiles", [])

    @property
    def peptide_summary_files(self) -> List[str]:
        """
        A list of PeptideSummary files to be processed.

        """
        return self._config.get("PeptideSummaryFiles", [])

    @property
    def quantitation_ratios(self) -> List[str]:
        """
        A list of the quantitation ratios to consider.

        """
        return self._config.get("QuantitationRatios", [])

    @property
    def peptide_conf_threshold(self) -> float:
        """
        The threshold on which to cut-off peptide identifications in the
        PeptideSummary files.

        """
        return self._config.get("PeptideConfidenceThreshold", 95)

    @property
    def min_num_spectra(self) -> int:
        """
        The minimum number of spectra required to include the quantitation
        results for a protein.

        """
        return self._config.get("MinimumNumberOfSpectra", 4)

    @property
    def results_dir(self) -> str:
        """
        The directory within which to store all generated files.

        """
        return self._config["ResultsDirectory"]

    def validate(self):
        """
        Validates the input configuration to check for obvious problems such
        as missing files, missing required options and lack of uniqueness
        among keys.

        Raises:
            ConfigError

        """
        errors: List[str] = []
        errors.extend(self._validate_protein_summary_files())
        errors.extend(self._validate_peptide_summary_files())
        errors.extend(self._validate_quantitation_ratios())
        if errors:
            raise ConfigError("\n".join(errors))

    def _validate_protein_summary_files(self) -> List[str]:
        """
        """
        return _validate_file_list(self.protein_summary_files)

    def _validate_peptide_summary_files(self) -> List[str]:
        """
        Validates the input to the PeptideSummaryFiles option.

        """
        return _validate_file_list(self.peptide_summary_files)

    def _validate_quantitation_ratios(self) -> List[str]:
        """
        Validates the input to QuantitationRatios, checking each is one of
        the valid options.

        """
        errors: List[str] = []
        for ratio in self.quantitation_ratios:
            if any((t not in ITRAQ_TAGS for t in ratio.split(":"))):
                errors.append(f"Invalid quantitation ratio: {ratio}")
        return errors
