#! /usr/bin/env python3

import os

import pandas as pd

from .quantify_config import QuantifyConfig
from .utilities import read_tsv


OUTPUT_FILE_NAME = "AccessionProteinNames.csv"


class Accessions:
    """
    """
    def __init__(self, config_file: str):
        """
        """
        self._config = QuantifyConfig(config_file)

        self._merged_dir = os.path.join(self._config.results_dir, "group")

    def merge_protein_names(self):
        """
        Merges the accession to protein name maps from all input ProteinSummary
        files to a single output file.

        """
        merged_df = pd.concat([read_tsv(f, usecols=["Accession", "Name"])
                               for f in self._config.protein_summary_files])

        if not os.path.exists(self._merged_dir):
            os.makedirs(self._merged_dir)

        target_file = os.path.join(self._merged_dir, OUTPUT_FILE_NAME)
        merged_df.to_csv(target_file, sep="\t", index=False)
