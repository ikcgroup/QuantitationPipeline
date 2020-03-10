#! /usr/bin/env python3

import os

from quantify_proteins import QuantifyConfig


TEST_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_CONFIG_DIR = os.path.join(TEST_DIR, "test_configs")


def build_config(
        results_dir=None,
        protein_summary_files=None,
        peptide_summary_files=None,
        quantitation_ratios=None,
        peptide_conf_threshold=None,
        min_num_spectra=None) -> QuantifyConfig:
    """
    """
    data = {}
    if results_dir is not None:
        data["ResultsDirectory"] = results_dir
    if protein_summary_files is not None:
        data["ProteinSummaryFiles"] = protein_summary_files
    if peptide_summary_files is not None:
        data["PeptideSummaryFiles"] = peptide_summary_files
    if quantitation_ratios is not None:
        data["QuantitationRatios"] = quantitation_ratios
    if peptide_conf_threshold is not None:
        data["PeptideConfidenceThreshold"] = peptide_conf_threshold
    if min_num_spectra is not None:
        data["MinimumNumberOfSpectra"] = min_num_spectra

    return QuantifyConfig.from_dict(data)
