#! /usr/bin/env python3

import logging
import multiprocessing as mp
import os
import re
from typing import List

import pandas as pd

from .fdr import get_fdr_name, read_fdr_value
from .quantify_config import ConfigError, QuantifyConfig
from .utilities import get_file_id, read_tsv, reversed_enumerate, split_to_set


LOGGER = logging.getLogger(__name__)

HASH_REMOVE_REGEX = re.compile(r"-like|isoform X\d+ |\d+\w+")


class CoWinner:
    """
    """
    def __init__(self, config_file: str):
        """
        Initialize the CoWinner object.

        """
        self._config = QuantifyConfig(config_file)

        self._output_dir = os.path.join(self._config.results_dir, "cowinner")
        self._merged_dir = os.path.join(self._output_dir, "merged")

    def validate_config(self):
        """
        Validates the configuration file to ensure that input is appropriate
        for use.

        Raises:
            ConfigError

        """
        self._config.validate()

    def evaluate(self):
        """
        """
        prot_summary_files = self._config.protein_summary_files
        if not prot_summary_files:
            raise ConfigError("No ProteinSummary files configured")

        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir)

        LOGGER.info("Starting cowinner evaluation")

        with mp.Pool(processes=4) as pool:
            pool.map(self._process_protein_summary, prot_summary_files)
            pool.close()
            pool.join()

        LOGGER.info("All files processed")

    def _process_protein_summary(self, summary_file: str):
        """
        Processes the given ProteinSummary file by extracting the protein
        identifications which pass local FDR control and deduplicating based
        on the Total value, combining accessions into a single line.

        Args:
            summary_file (str): The path to the ProteinSummary file.

        """
        fdr_path = get_fdr_name(summary_file)

        # The number of protein identifications passing critical local FDR
        n_pass_fdr = read_fdr_value(fdr_path, 5)

        prot_df = read_tsv(summary_file)
        prot_df = reduce_df(prot_df, n_pass_fdr)
        prot_df.to_csv(
                os.path.join(self._output_dir, os.path.basename(summary_file)),
                sep="\t", index=False)

    def merge(self):
        """
        """
        cowinner_files = [os.path.join(self._output_dir, f)
                          for f in next(os.walk(self._output_dir))[2]
                          if not f.startswith(".")]
        cowinner_files.sort()

        base_df = read_tsv(cowinner_files[0])

        base_df.insert(0, "Expr Date", get_file_id(cowinner_files[0]))
        base_df.Accession = split_to_set(base_df.Accession, "; ")

        for cw_file in cowinner_files[1:]:
            df = read_tsv(cw_file)
            df["Expr Date"] = get_file_id(cw_file)
            df.Accession = split_to_set(df.Accession, "; ")
            base_df = _merge_to_base(df, base_df)

        base_accs = list(base_df.Accession)

        # Check for duplicates across experiments after merge by performing
        # backwards pairwise comparison of the merged rows
        keep = [True] * len(base_accs)
        for ii, accs in reversed_enumerate(base_accs):
            for jj, accs2 in reversed_enumerate(base_accs[:ii]):
                if accs & accs2:
                    keep[ii] = False
                    base_accs[jj] = accs | accs2

        base_df.Accession = base_accs
        base_df = base_df[keep]

        # Convert accessions back to strings for output
        base_df.Accession = base_df.Accession.map(
                lambda a: "; ".join(sorted(a)))

        if not os.path.exists(self._merged_dir):
            os.makedirs(self._merged_dir)

        base_df.to_csv(os.path.join(self._merged_dir, "merged.csv"), sep="\t",
                       index=False)


def _merge_to_base(source_df: pd.DataFrame, target_df: pd.DataFrame):
    """
    """
    src_accs = list(source_df.Accession)
    tgt_accs = list(target_df.Accession)

    add_row_idxs: List[int] = []

    for ii, src in enumerate(src_accs):
        for jj, tgt in enumerate(tgt_accs):
            if src & tgt:
                tgt_accs[jj] = src | tgt
                break
        else:
            add_row_idxs.append(ii)

    target_df.Accession = tgt_accs

    if add_row_idxs:
        target_df = pd.concat([target_df, source_df.iloc[add_row_idxs]],
                              ignore_index=True)

    return target_df


def join_top_accessions(df: pd.DataFrame) -> str:
    """
    Combines the accessions of rows with a Total value equal to the first row
    of the group.

    Args:
        df (pd.DataFrame): A DataFrame for which row accessions should be
                           merged to a single string.

    Returns:
        string

    """
    return "; ".join(
        df.loc[df.Total == df.Total[0], "Accession"].sort_values())


def reduce_df(df: pd.DataFrame, max_n: int) -> pd.DataFrame:
    """
    Reduces the DataFrame by grouping on N and retaining only those rows
    whose Total value matches the first row in the group. For the retained
    rows, the Accession values are merged to a single string.

    Args:
        df (pd.DataFrame): DataFrame parsed from ProteinSummary TSV.
        max_n (int): The number of protein identifications which passed local
                     FDR control.

    Returns:
        pd.DataFrame: The reduced DataFrame.

    """
    df = df[df.N <= max_n]
    dedup_df = df.drop_duplicates("N", keep="first").copy()\
                 .reset_index(drop=True)
    dedup_df.Accession = df.groupby("N")\
                           .apply(join_top_accessions).reset_index()[0]
    return dedup_df
