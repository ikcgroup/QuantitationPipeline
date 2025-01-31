#! /usr/bin/env python3
"""
This module defines the Quantifier class for analyzing ProteinPilot
quantitation data.

"""

import itertools
import logging
import math
import multiprocessing as mp
import os
import re
from typing import Callable, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import scipy.stats

from .appbase import AppBase
from .fdr import get_fdr_name, read_fdr_value
from .quantify_config import ConfigError
from .utilities import get_file_id, ordered_value_counts, read_accession_names,\
    read_tsv


LOGGER = logging.getLogger(__name__)

OUTPUT_INSERT = " hkuNoBgCorr"
GROUP_OUTPUT_INSERT = f"{OUTPUT_INSERT} MultiNormalize"


def get_quant_output_file_name(summary_path: str, tag_ratio: str,
                               insert: str = OUTPUT_INSERT) -> str:
    """
    Generates the name of the output Excel file based on the input
    PeptideSummary file and the iTRAQ tag ratio.

    Args:
        summary_path (str): The path to the input PeptideSummary file.
        tag_ratio (str): The iTRAQ ratio, e.g. 114:113.

    Returns:
        str

    """
    ratio_str = tag_ratio.replace(":", "-")
    return os.path.basename(summary_path).replace(
        "_PeptideSummary.txt",
        f"_{ratio_str}_PeptideSummary{insert}.xlsx")


def get_quant_group_output_file_name(summary_path: str, tag_ratio: str) -> str:
    """
    Generates the name of the output Excel file based on the input
    PeptideSummary file and the iTRAQ tag ratio.

    Args:
        summary_path (str): The path to the input PeptideSummary file.
        tag_ratio (str): The iTRAQ ratio, e.g. 114:113.

    Returns:
        str

    """
    return get_quant_output_file_name(summary_path, tag_ratio,
                                      insert=GROUP_OUTPUT_INSERT)


def replace_accessions(base_df: pd.DataFrame, match_df: pd.DataFrame) \
        -> pd.DataFrame:
    """

    Args:
        base_df:
        match_df:

    Returns:
        pd.DataFrame

    """
    # In the DataFrame to match against, create a new column, "Accessions",
    # as a list of accession IDs, then "explode" into separate rows
    temp_df = match_df.assign(Accessions=match_df.Accession.str.split("; ")).\
        explode("Accessions")
    base_df = base_df.merge(temp_df[["Accession", "Accessions"]],
                            on="Accessions")
    base_df.Accessions = base_df.pop("Accession")
    return base_df.sort_values(["Expt", "N"])


def _ln_normalized_col(ratio):
    """

    Args:
        ratio:

    Returns:
        str

    """
    return f"ln(normalized {ratio})"


def _normalized_col(ratio):
    """

    Args:
        ratio:

    Returns:
        str

    """
    return f"normalized {ratio}"


class Quantifier(AppBase):
    """
    A class to provide methods for quantifying the proteins identified
    in the configured data.

    """
    # Common columns
    ACCESSIONS_COL = "Accessions"

    # Peptide sheet columns
    ERR_RECIPROCAL_COL = "1/%Err"
    NORM_WEIGHT_COL = "Normalized weight"
    WX_COL = "wx"
    NEW_LN_RATIO_COL = "new ln ratio"

    # FDR sheet columns
    SUM_ERR_RECIPROCAL_COL = "Sum of (1/%Err)"
    PROT_SPECTRAL_WEIGHT_COL = "Protein spectral weight const"
    NUM_SPECTRA_COL = "No. of spectra"

    # Protein sheet columns
    SUM_WX_COL = "Sum of wx"
    SUM_NORM_WEIGHT_COL = "Sum of normalized weight"
    WEIGHTED_AVG_COL = "Weighted average"
    EXP_WEIGHTED_AVG_COL = "exp(weighted average)"
    NORM_PROTEIN_RATIO_COL = "Normalized protein ratio"
    ST_DEV_COL = "Standard deviation"
    T_VALUE_UP_COL = "t-value (up)"
    P_VALUE_UP_COL = "p-value (up)"
    T_VALUE_DOWN_COL = "t-value (down)"
    P_VALUE_DOWN_COL = "p-value (down)"

    BASE_GROUP_KEEP_COLS = ["Expt", "N", "Unused", ACCESSIONS_COL, "Spectrum"]

    # Constants
    T_UP_FACTOR = 1.23
    T_DOWN_FACTOR = 0.81

    def __init__(self, *args):
        """
        Initialize the class, passing the config to the base class.

        """
        super().__init__(*args)

        # The current iTRAQ tag ratio being processed
        self._ratio: Optional[str] = None

    def validate_config(self):
        """
        Validates the input configuration for quantitation. Note that this
        hides the AppBase implementation.

        """
        super().validate_config()
        if not self.config.peptide_summary_files:
            raise ConfigError("No PeptideSummary files configured")

    def quantify(self):
        """
        Performs quantitation analysis on the configured PeptideSummary files.

        Raises:
            ConfigError

        """
        LOGGER.info("Starting quantitation")

        summary_ratios = itertools.product(self.config.peptide_summary_files,
                                           self.config.quantitation_ratios)
        with mp.Pool(processes=4) as pool:
            pool.starmap(self._process_peptide_summary, summary_ratios)
            pool.close()
            pool.join()

        # Reset the class state
        self._ratio = None

        LOGGER.info("All PeptideSummary files processed")

    def quantify_group(self):
        """

        Returns:

        """
        LOGGER.info("Starting group quantitation")

        cowinner_merged_file = os.path.join(
            self.config.results_dir, "cowinner", "merged",
            self.config.cowinner_merge_output_file)
        cowinner_df = read_tsv(cowinner_merged_file)

        accession_names_map = read_accession_names(
            os.path.join(self.config.results_dir, "group",
                         self.config.accessions_output_file))

        for ratio in self.config.quantitation_ratios:
            self._process_ratio_quant_files(ratio, cowinner_df,
                                            accession_names_map)

    def _process_peptide_summary(self, peptide_summary: str, ratio: str):
        """
        Performs quantitation analysis on the given peptide_summary file
        for the specified iTRAQ ratio. The results are written out to an
        Excel spreadsheet.

        Args:
            peptide_summary (str): The path to the PeptideSummary file.
            ratio (str): The iTRAQ ratio to quantify.

        """
        # This is set here, rather than outside this method, so that it is
        # immediately configured on the new process spawned using the
        # multiprocessing Pool
        self._ratio = ratio

        summary_df = read_tsv(peptide_summary)

        n_passed_fdr = read_fdr_value(get_fdr_name(peptide_summary))

        summary_df = self._filter_peptides(summary_df, n_passed_fdr)

        peptide_df = self._setup_peptide_df(summary_df)
        peptide_df.insert(0, "Expt", get_file_id(peptide_summary))

        fdr_df = self._generate_fdr_df(peptide_df)

        peptide_df = self._update_peptide_df(peptide_df, fdr_df)

        protein_df = self._setup_protein_df(peptide_df, fdr_df)
        protein_df, exp_avg_wx_factor = self._update_protein_df(protein_df)

        peptide_df = self._finalize_peptide_df(peptide_df, exp_avg_wx_factor)

        protein_df = self._finalize_protein_df(protein_df, peptide_df)

        self._write_excel(
            os.path.join(
                self.config.results_dir,
                get_quant_output_file_name(peptide_summary, self._ratio)),
            {"Peptide": peptide_df, "Protein": protein_df,
             "FDR with 1 spectra": fdr_df, "Peptide Summary": summary_df})

    def _process_ratio_quant_files(self, ratio: str, cowinner_df: pd.DataFrame,
                                   accession_names_map: Dict[str, str]):
        """

        Args:
            ratio: The iTRAQ tag ratio for which to combine quantitation
                   results.

        """
        quantify_files = [get_quant_output_file_name(summary, ratio) for
                          summary in self.config.peptide_summary_files]

        ln_norm_ratio_col = _ln_normalized_col(ratio)
        keep_cols = self.BASE_GROUP_KEEP_COLS +\
            [_normalized_col(ratio), ln_norm_ratio_col,
             self.ERR_RECIPROCAL_COL]

        peptide_df = pd.concat(
            [pd.read_excel(os.path.join(self.config.results_dir, qf),
                           sheet_name="Peptide")[keep_cols]
             for qf in quantify_files], ignore_index=True)

        peptide_df = replace_accessions(peptide_df, cowinner_df)

        fdr_df = self._generate_fdr_df(peptide_df)\
            .sort_values(self.ACCESSIONS_COL)

        peptide_df[self.NORM_WEIGHT_COL] = \
            self._calculate_normalized_weight(peptide_df, fdr_df)
        peptide_df[self.WX_COL] = peptide_df[ln_norm_ratio_col] * \
            peptide_df[self.NORM_WEIGHT_COL]

        # TODO: Seems that this is the same as the wx column when using
        #       the ln(normalized [ratio]) column?
        peptide_df[self.NEW_LN_RATIO_COL] = peptide_df[ln_norm_ratio_col] * \
            peptide_df[self.NORM_WEIGHT_COL]

        protein_df = self._finalize_protein_df(
            self._setup_protein_df(peptide_df, fdr_df), peptide_df,
            protein_ratio_col=self.EXP_WEIGHTED_AVG_COL)

        protein_df = self._add_protein_names(protein_df, accession_names_map)

        self._write_excel(
            os.path.join(
                self.config.results_dir,
                get_quant_group_output_file_name(
                    self.config.peptide_summary_files[0], ratio)),
            {"Peptide": peptide_df, "Protein": protein_df,
             "FDR with 1 spectra": fdr_df})

    def _filter_peptides(self, df: pd.DataFrame, max_n: int) -> pd.DataFrame:
        """
        Filters the PeptideSummary DataFrame to only those identifications
        which are to be used during quantitation.

        Args:
            df (pd.DataFrame): The PeptideSummary DataFrame.
            max_n (int): The last protein ID to pass local protein FDR.

        Returns:
            pd.DataFrame

        """
        return df[
            # Remove peptides not mapped to a protein which passes protein
            # level FDR
            (df.N <= max_n) &
            # Remove peptides which don't pass the configured confidence
            # threshold
            (df.Conf >= self.config.peptide_conf_threshold) &
            # Keep only the peptides ProteinPilot used for quantitation
            (df.Used == 1) &
            # Keep only the peptides with valid quantitation ratios for the
            # configured reporter ions
            (df[self._ratio] != 100.)]

    #
    # Peptide DataFrame
    #
    def _setup_peptide_df(self, summary_df: pd.DataFrame)\
            -> pd.DataFrame:
        """
        Initializes the peptide DataFrame using the filtered PeptideSummary
        information.

        Args:
            summary_df (pd.DataFrame): The filtered PeptideSummary DataFrame.

        Returns:
            pd.DataFrame

        """
        ratio_err_col = f"%Err {self._ratio}"
        peptide_df = summary_df[
            ["N", "Unused", "Accessions", "Spectrum", self._ratio,
             ratio_err_col]].copy().reset_index(drop=True)

        ratio_ln_col = f"ln({self._ratio})"
        peptide_df[ratio_ln_col] = np.log(peptide_df[self._ratio])
        peptide_df[self.ERR_RECIPROCAL_COL] = 1 / peptide_df[ratio_err_col]

        return peptide_df

    def _update_peptide_df(self, peptide_df: pd.DataFrame,
                           fdr_df: pd.DataFrame) -> pd.DataFrame:
        """
        Updates the peptide DataFrame using information calculated in the
        FDR DataFrame.

        Args:
            peptide_df (pd.DataFrame): The peptide DataFrame.
            fdr_df (pd.DataFrame): The FDR DataFrame.

        Returns:
            pd.DataFrame

        """
        peptide_df[self.NORM_WEIGHT_COL] = \
            self._calculate_normalized_weight(peptide_df, fdr_df)
        peptide_df[self.WX_COL] = peptide_df[f"ln({self._ratio})"] * \
            peptide_df[self.NORM_WEIGHT_COL]
        return peptide_df

    def _finalize_peptide_df(self, peptide_df: pd.DataFrame,
                             wx_norm_factor: float) -> pd.DataFrame:
        """
        Calculates the remaining fields in the peptide dataframe.

        Note: this must be called after _setup_protein_df has been used to
        initialize the protein dataframe and calculate wx_norm_factor.

        Args:
            peptide_df (pd.DataFrame): The peptide DataFrame.
            wx_norm_factor (float): The computed wx normalization factor, from
                                    calculations on the protein DataFrame.

        Returns:
            pd.DataFrame

        """
        norm_ratio_col = _normalized_col(self._ratio)
        peptide_df[norm_ratio_col] = peptide_df[self._ratio] / wx_norm_factor

        ln_norm_ratio_col = f"ln({norm_ratio_col})"
        peptide_df[ln_norm_ratio_col] = np.log(peptide_df[norm_ratio_col])

        peptide_df[self.NEW_LN_RATIO_COL] = peptide_df[ln_norm_ratio_col] *\
            peptide_df[self.NORM_WEIGHT_COL]

        return peptide_df

    #
    # FDR with 1 Spectra DataFrame
    #
    def _generate_fdr_df(self, peptide_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates the FDR DataFrame, using the peptide DataFrame for
        computations.

        Args:
            peptide_df (pd.DataFrame): The peptide DataFrame.

        Returns:
            pd.DataFrame

        """
        fdr_df = ordered_value_counts(peptide_df.Accessions,
                                      name=self.NUM_SPECTRA_COL)
        fdr_df = self._sum_error_reciprocal(peptide_df, fdr_df)
        fdr_df[self.PROT_SPECTRAL_WEIGHT_COL] = \
            self._calculate_protein_spectral_weight(fdr_df)
        return fdr_df

    #
    # Protein DataFrame
    #
    def _setup_protein_df(self, peptide_df: pd.DataFrame,
                          fdr_df: pd.DataFrame) -> pd.DataFrame:
        """
        Initializes the protein DataFrame using information stored/calculated
        for peptides and FDR purposes. Note that some fields are calculated
        later as they rely on further peptide details (a cyclic dependency
        exists between the Excel worksheets output by the original quantitation
        pipeline).

        Args:
            peptide_df (pd.DataFrame): The peptide DataFrame.
            fdr_df (pd.DataFrame): The FDR DataFrame.

        Returns:


        """
        protein_df = fdr_df[fdr_df[self.NUM_SPECTRA_COL]
                            >= self.config.min_num_spectra].copy()
        protein_df = self._sum_wx(peptide_df, protein_df)
        protein_df = self._sum_norm_weight(peptide_df, protein_df)
        protein_df[self.WEIGHTED_AVG_COL] = protein_df[self.SUM_WX_COL] /\
            protein_df[self.SUM_NORM_WEIGHT_COL]
        protein_df[self.EXP_WEIGHTED_AVG_COL] =\
            np.exp(protein_df[self.WEIGHTED_AVG_COL])

        return protein_df

    def _update_protein_df(self, protein_df: pd.DataFrame) \
            -> Tuple[pd.DataFrame, float]:
        """
        Updates the peptide DataFrame. This is separated out from
        _setup_protein_df as these columns are not required when grouping
        quantitation results.

        Args:
            protein_df: The protein DataFrame.

        Returns:
            Tuple of (pd.DataFrame, float), where the DataFrame is the protein
            DataFrame and the float is the wx normalization factor.

        """
        median_exp_avg = np.median(protein_df[self.EXP_WEIGHTED_AVG_COL])

        protein_df[self.NORM_PROTEIN_RATIO_COL] = \
            protein_df[self.EXP_WEIGHTED_AVG_COL] / median_exp_avg

        return protein_df, median_exp_avg

    def _finalize_protein_df(self, protein_df: pd.DataFrame,
                             peptide_df: pd.DataFrame,
                             protein_ratio_col: str = NORM_PROTEIN_RATIO_COL)\
            -> pd.DataFrame:
        """
        Finalizes calculations on the protein DataFrame, using information
        in the associated peptide DataFrame.

        Args:
            protein_df (pd.DataFrame): The initialized protein DataFrame.
            peptide_df (pd.DataFrame): The peptide DataFrame.

        Returns:
            pd.DataFrame

        """
        protein_df = self._apply_col_merge(peptide_df, protein_df,
                                           self.NEW_LN_RATIO_COL,
                                           self.ST_DEV_COL,
                                           lambda d: d.std())

        deg_freedom = protein_df[self.NUM_SPECTRA_COL] - 1

        protein_df[self.T_VALUE_UP_COL] = self._t_value(
            protein_df, self.T_UP_FACTOR, protein_ratio_col=protein_ratio_col)

        protein_df[self.P_VALUE_UP_COL] = \
            1. - scipy.stats.t.cdf(protein_df[self.T_VALUE_UP_COL], deg_freedom)

        protein_df[self.T_VALUE_DOWN_COL] = \
            self._t_value(protein_df, self.T_DOWN_FACTOR,
                          protein_ratio_col=protein_ratio_col)

        protein_df[self.P_VALUE_DOWN_COL] = \
            scipy.stats.t.cdf(protein_df[self.T_VALUE_DOWN_COL], deg_freedom)

        return protein_df

    def _add_protein_names(self, protein_df: pd.DataFrame,
                           accession_names_map: Dict[str, str]) -> pd.DataFrame:
        """

        Args:
            protein_df:
            accession_names_map:

        Returns:

        """
        protein_df["Names"] = protein_df[self.ACCESSIONS_COL]
        for accession, protein in accession_names_map.items():
            protein_df["Names"] =\
                protein_df["Names"].str.replace(re.escape(accession), protein)
        return protein_df

    #
    # Helper methods
    #
    def _write_excel(self, output_file: str,
                     sheet_dfs: Dict[str, pd.DataFrame]):
        """
        Writes the input DataFrames to a single Excel file.

        Args:
            output_file (str): The file to which output should be written.
            sheet_dfs (dict): A map of output sheet name to the DataFrame to be
                              written to said sheet.

        """
        with pd.ExcelWriter(output_file) as writer:
            for sheet, out_df in sheet_dfs.items():
                out_df.to_excel(writer, sheet_name=sheet, index=False)

    def _t_value(self, protein_df: pd.DataFrame, factor: float,
                 protein_ratio_col: str = NORM_PROTEIN_RATIO_COL) -> pd.Series:
        """
        Calculates the t-test value on the normalized protein ratios, using
        the specified factor for up/down significance testing.

        Args:
            protein_df (pd.DataFrame): The protein DataFrame.
            factor (float): A factor to be logged and subtracted from the
                            log of the normalized protein ratios.

        Returns:
            pd.Series

        """
        return (np.log(protein_df[protein_ratio_col]) -
                math.log(factor)) /\
               (protein_df[self.ST_DEV_COL] /
                np.sqrt(protein_df[self.SUM_NORM_WEIGHT_COL]))

    def _apply_col_merge(self, source_df: pd.DataFrame,
                         target_df: pd.DataFrame, col: str, rename_col: str,
                         apply_func: Callable[[pd.core.groupby.GroupBy],
                                              pd.DataFrame]) -> pd.DataFrame:
        """
        Applies a pd.DataFrameGroupBy method to the source_df, grouped on the
        Accessions column, then merges the new values to target_df using the
        new column name (rename_col).

        Args:
            source_df (pd.DataFrame): The DataFrame containing col.
            target_df (pd.DataFrame): The DataFrame to which the calculated
                                      values should be merged.
            col (str): The name of the column to which apply_func is applied.
            rename_col (str): The new name of the resulting column in the
                              returned DataFrame.
            apply_func: A function which takes a DataFrameGroupBy object and
                        returns the result of executing one of the associated
                        methods (e.g. .sum(), .std()).

        """
        res = source_df[[self.ACCESSIONS_COL, col]]\
            .groupby(source_df[self.ACCESSIONS_COL])\
            .pipe(apply_func)\
            .reset_index()\
            .rename(columns={col: rename_col})
        return target_df.merge(res, on=self.ACCESSIONS_COL)

    def _sum_col_merge(self, sum_df: pd.DataFrame, target_df: pd.DataFrame,
                       sum_col: str, rename_col: str) -> pd.DataFrame:
        """
        Calculates the summation of the sum_col values, grouping by the
        protein accessions, then merges summed values to target_df on the
        accession values.

        Args:
            sum_df (pd.DataFrame): The DataFrame containing sum_col.
            target_df (pd.DataFrame): The DataFrame to which the summed values
                                      should be merged.
            sum_col (str): The name of the column to sum.
            rename_col (str): The new name of the summed column in the returned
                              DataFrame.

        Returns:
            pd.DataFrame

        """
        return self._apply_col_merge(sum_df, target_df, sum_col, rename_col,
                                     lambda d: d.sum())

    #
    # FDR worksheet calculations
    #
    def _sum_error_reciprocal(self, peptide_df: pd.DataFrame,
                              fdr_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates the sum of the reciprocal errors in the peptide_df, grouped
        by accession, and stores the output in the fdr_df.

        Args:
            peptide_df (pd.DataFrame): The peptide DataFrame.
            fdr_df (pd.DataFrame): The FDR DataFrame.

        Returns:
            pd.DataFrame: The FDR DataFrame with a new column
            (SUM_ERR_RECIPROCAL_COL).

        """
        return self._sum_col_merge(peptide_df, fdr_df, self.ERR_RECIPROCAL_COL,
                                   self.SUM_ERR_RECIPROCAL_COL)

    def _calculate_protein_spectral_weight(self, fdr_df: pd.DataFrame) \
            -> pd.Series:
        """
        Calculates the protein spectral weights.

        Args:
            fdr_df (pd.DataFrame): The FDR DataFrame.

        Returns:
            pd.Series

        """
        return fdr_df[self.NUM_SPECTRA_COL] /\
            fdr_df[self.SUM_ERR_RECIPROCAL_COL]

    #
    # Peptide worksheet calculations
    #
    def _calculate_normalized_weight(self, peptide_df: pd.DataFrame,
                                     fdr_df: pd.DataFrame) -> pd.Series:
        """
        Calculates the normalized spectral weight.

        Args:
            peptide_df (pd.DataFrame): The peptide DataFrame.
            fdr_df (pd.DataFrame): The FDR DataFrame.

        Returns:
            pd.Series

        """
        merged_df = peptide_df.merge(fdr_df, on=self.ACCESSIONS_COL)
        return peptide_df[self.ERR_RECIPROCAL_COL] * \
            merged_df[self.PROT_SPECTRAL_WEIGHT_COL]

    #
    # Protein worksheet calculations
    #
    def _sum_wx(self, peptide_df: pd.DataFrame,
                protein_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates the sum of wx in the peptide DataFrame, grouped by
        accession.

        Args:
            peptide_df (pd.DataFrame): The peptide DataFrame.
            protein_df (pd.DataFrame): The protein DataFrame.

        Returns:
            pd.DataFrame: The protein DataFrame with an additional column
            (SUM_WX_COL).

        """
        return self._sum_col_merge(peptide_df, protein_df, self.WX_COL,
                                   self.SUM_WX_COL)

    def _sum_norm_weight(self, peptide_df: pd.DataFrame,
                         protein_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates the sum of the normalized weights in the peptide DataFrame,
        grouped by accession.

        Args:
            peptide_df (pd.DataFrame): The peptide DataFrame.
            protein_df (pd.DataFrame): The protein DataFrame.

        Returns:
            pd.DataFrame: The protein DataFrame with an additional column
            (SUM_NORM_WEIGHT_COL).

        """
        return self._sum_col_merge(peptide_df, protein_df,
                                   self.NORM_WEIGHT_COL,
                                   self.SUM_NORM_WEIGHT_COL)
