#! /usr/bin/env python3
"""
"""
from typing import Dict, Tuple

import xlrd


# The critical FDR values present in the ProteinPilot FDR output
CRITICAL_FDR_CELLS: Dict[int, Tuple[int, int]] = {
    1: (5, 2),
    5: (6, 2),
    10: (7, 2)
}


def get_fdr_name(summary_name: str) -> str:
    """
    Infers the name of the FDR Excel spreadsheet based on that of the input
    Protein/Peptide Summary file.

    Args:
        summary_name (str): The path to a ProteinSummary/PeptideSummary file.

    Returns:
        The name of the corresponding FDR Excel spreadsheet.

    Raises:
        ValueError

    """
    idx = summary_name.find("ProteinSummary")
    if idx == -1:
        idx = summary_name.find("PeptideSummary")
    if idx == -1:
        raise ValueError(f"File name {summary_name} does not contain "
                         "ProteinSummary or PeptideSummary")
    return f"{summary_name[:idx]}_FDR.xlsx"


def read_fdr_value(fdr_name: str, crit_fdr: int = 5) -> int:
    """
    """
    if crit_fdr not in CRITICAL_FDR_CELLS:
        raise ValueError(f"Critical FDR value {crit_fdr} not in acceptable "
                         f"set of {', '.join(CRITICAL_FDR_CELLS.keys())}")

    book = xlrd.open_workbook(fdr_name, on_demand=True)
    sheet = book.sheet_by_name("Protein Level Summary")
    fdr_value = sheet.cell_value(*CRITICAL_FDR_CELLS[crit_fdr])
    book.release_resources()
    return int(fdr_value)
