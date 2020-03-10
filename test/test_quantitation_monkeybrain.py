#! /usr/bin/env python3

import itertools
import os
import unittest

import pandas as pd

from quantify_proteins import ConfigError, Quantifier
from quantify_proteins.quantitation import get_output_file_name


TEST_CONFIG_FILE = "test_config_mb.json"
BENCHMARK_DIR = os.path.join("test_data", "monkey_brain", "benchmarks")
SHEET_NAMES = ["Peptide", "Protein", "FDR with 1 spectra", "Peptide Summary"]

EXCEL_ENGINE = "openpyxl"


def read_excel_sheet(excel_file: str, sheet: str):
    """
    Reads the specified sheet of the given excel_file, using the globally
    configured engine.

    """
    return pd.read_excel(excel_file, sheet_name=sheet, engine=EXCEL_ENGINE)


class MonkeyBrainQuantitationTests(unittest.TestCase):
    def test_monkeybrain_quantitation(self):
        quantifier = Quantifier(TEST_CONFIG_FILE)
        try:
            quantifier.validate_config()
        except ConfigError as e:
            self.fail(e.message)

        quantifier.quantify()

        summary_ratios = itertools.product(
            quantifier._config.peptide_summary_files,
            quantifier._config.quantitation_ratios)
        for pep_summary, ratio in summary_ratios:
            output_file = get_output_file_name(pep_summary, ratio)
            output_path = os.path.join(
                quantifier._config.results_dir, output_file)

            benchmark_path = os.path.join(BENCHMARK_DIR, output_file)

            for sheet in SHEET_NAMES:
                df = read_excel_sheet(output_path, sheet)
                benchmark_df = read_excel_sheet(benchmark_path, sheet)

                if sheet == "Peptide":
                    # Don't compare the "Expt" column as this is now produced
                    # differently compared to the C# version of the pipeline
                    df = df.drop(columns=["Expt"])
                    benchmark_df = benchmark_df.drop(columns=["Expt"])
                elif sheet == "Protein":
                    # Since the benchmarked results depend on a value computed
                    # in Protein!$P$2, the additional two columns should be
                    # dropped before comparison - this value is no longer
                    # stored in the output
                    benchmark_df = benchmark_df.iloc[:, 0:14]

                print(f"Testing {pep_summary}, {ratio}, {sheet} frames...")
                # check_exact is set to False in order to ignore small
                # differences in calculated values, less than the comparison
                # precision of 4 decimal places
                pd.testing.assert_frame_equal(
                    df, benchmark_df, check_exact=False, check_less_precise=4)
