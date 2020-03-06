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


def get_fdr_name(prot_summary_name: str) -> str:
    """
    """
    idx = prot_summary_name.find("ProteinSummary")
    if idx == -1:
        raise ValueError(f"File name {prot_summary_name} does not contain "
                         "ProteinSummary")
    return f"{prot_summary_name[:idx]}_FDR.xlsx"


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
