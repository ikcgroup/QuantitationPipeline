#! /usr/bin/env python3

import os
import shutil
import unittest

import pandas as pd

from quantify_proteins import Accessions, QuantifyConfig
from quantify_proteins.accessions import OUTPUT_FILE_NAME
from quantify_proteins.utilities import dir_exists, read_tsv

from .test_common import TEST_CONFIG_DIR


TEST_CONFIG_FILE = os.path.join(TEST_CONFIG_DIR, "test_config.json")

BENCHMARK_DIR = os.path.join("test_data", "6hr data", "group")
BENCHMARK_FILE = "hkuAccessionProtName.txt"


def sort_accessions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sorts the input DataFrame by the accessions.

    Args:
        df (pd.DataFrame): The DataFrame to sort.

    Returns:
        pd.DataFrame

    """
    return df.sort_values("Accession").reset_index(drop=True)


class AccessionTests(unittest.TestCase):
    def setUp(self):
        config = QuantifyConfig.from_file(TEST_CONFIG_FILE)

        # Tidy up output directories - test directory creation
        if dir_exists(config.results_dir):
            shutil.rmtree(config.results_dir)

    def test_merge(self):
        accessions = Accessions(TEST_CONFIG_FILE)

        accessions.merge_protein_names()

        res_df = read_tsv(os.path.join(accessions.merged_dir,
                                       OUTPUT_FILE_NAME))

        bench_df = read_tsv(os.path.join(BENCHMARK_DIR, BENCHMARK_FILE),
                            names=["Accession", "Name"])

        pd.testing.assert_frame_equal(
                sort_accessions(res_df), sort_accessions(bench_df))


if __name__ == "__main__":
    unittest.main()
