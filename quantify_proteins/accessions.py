#! /usr/bin/env python3

import os

import pandas as pd

from .appbase import AppBase
from .utilities import dir_exists, read_tsv


OUTPUT_FILE_NAME = "AccessionProteinNames.csv"


class Accessions(AppBase):
    """
    A class containing methods related to the generation of an accession -
    protein name map.

    """
    def __init__(self, *args):
        """
        """
        super().__init__(*args)

        self.merged_dir = os.path.join(self.config.results_dir, "group")

    def merge_protein_names(self):
        """
        Merges the accession to protein name maps from all input ProteinSummary
        files to a single output file.

        """
        merged_df = pd.concat([read_tsv(f, usecols=["Accession", "Name"])
                               for f in self.config.protein_summary_files])

        if not dir_exists(self.merged_dir):
            os.makedirs(self.merged_dir)

        target_file = os.path.join(self.merged_dir, OUTPUT_FILE_NAME)
        merged_df.to_csv(target_file, sep="\t", index=False)
