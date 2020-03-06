#! /usr/bin/env python3

import os
from typing import Sequence

import pandas as pd


def get_file_id(file_path: str) -> str:
    """
    """
    return os.path.basename(file_path)[:8]


def read_tsv(file_path: str) -> pd.DataFrame:
    """
    Reads the given tab-separated file using Pandas.

    Args:
        file_path (str): The path to the tab-separated file.

    Returns:
        pd.DataFrame

    """
    return pd.read_csv(file_path, sep="\t")


def reversed_enumerate(sequence: Sequence):
    """
    """
    return reversed(list(enumerate(sequence)))


def split_to_set(series: pd.Series, sep: str) -> pd.Series:
    """
    """
    return series.str.split("; ").map(set)
