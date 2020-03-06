#! /usr/bin/env python3

import os
import unittest

import pandas as pd

from quantify_proteins import Accessions
from quantify_proteins.accessions import OUTPUT_FILE_NAME
from quantify_proteins.utilities import read_tsv


TEST_CONFIG_FILE = "test_config.json"
BENCHMARK_DIR = os.path.join("test_data", "6hr data", "group")
BENCHMARK_FILE = "hkuAccessionProtName.txt"


def sort_accessions(df: pd.DataFrame):
    """
    """
    return df.sort_values("Accession").reset_index(drop=True)


class AccessionTests(unittest.TestCase):
    def test_merge(self):
        accessions = Accessions(TEST_CONFIG_FILE)
        accessions.merge_protein_names()

        res_df = read_tsv(os.path.join(accessions._merged_dir,
                                       OUTPUT_FILE_NAME))

        bench_df = read_tsv(os.path.join(BENCHMARK_DIR, BENCHMARK_FILE),
                            names=["Accession", "Name"])

        pd.testing.assert_frame_equal(
                sort_accessions(res_df), sort_accessions(bench_df))


if __name__ == "__main__":
    unittest.main()
