#! /usr/bin/env python3

from typing import List


def accessions_by_semicolon(acc_str: str) -> List[str]:
    """
    """
    accs: List[str] = [s.strip() for s in acc_str.split(";") if s]
    accs.sort()
    return accs


def accession_by_semicolon(acc_str: str) -> str:
    """
    """
    return ";".join(accessions_by_semicolon(acc_str))
