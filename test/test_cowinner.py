#! /usr/bin/env python3

import os
import shutil
import unittest

import pandas as pd

from quantify_proteins import CoWinner


BENCHMARK_DIR = os.path.join("test_data", "6hr data", "cowinner")
TEST_CONFIG_FILE = "test_config.json"
RESULTS_DIR = os.path.join("test_data", "results", "cowinner")
MERGE_BENCHMARK_FILE = os.path.join(
    BENCHMARK_DIR, "merge", "20130512_nonphos_ProteinSummary_113 Merge.txt")


def read_tsv(tsv_file: str) -> pd.DataFrame:
    return pd.read_csv(tsv_file, sep="\t")


class CoWinnerTests(unittest.TestCase):
    def setUp(self):
        if os.path.exists(RESULTS_DIR):
            shutil.rmtree(RESULTS_DIR)
            os.makedirs(RESULTS_DIR)

    def test_cowinner(self):
        co_winner = CoWinner(TEST_CONFIG_FILE)
        try:
            co_winner.validate_config()
        except ConfigError as e:
            self.fail(e.message)

        try:
            co_winner.evaluate()
        except ConfigError as e:
            self.fail(e.message)

        for prot_summary in co_winner._config.protein_summary_files:
            summary_name = os.path.basename(prot_summary)
            res_file = os.path.join(RESULTS_DIR, summary_name)
            self.assertTrue(os.path.exists(res_file))

            benchmark_file = os.path.join(BENCHMARK_DIR, summary_name)
            self.assertTrue(os.path.exists(benchmark_file))

            pd.testing.assert_frame_equal(read_tsv(res_file),
                                          read_tsv(benchmark_file))

        co_winner.merge()

        merged_df = read_tsv(os.path.join(co_winner._merged_dir, "merged.csv"))
        benchmark_df = read_tsv(MERGE_BENCHMARK_FILE)

        pd.testing.assert_frame_equal(merged_df, benchmark_df)


if __name__ == "__main__":
    unittest.main()
