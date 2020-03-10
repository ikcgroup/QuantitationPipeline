#! /usr/bin/env python3

import os
from typing import Optional, Sequence

import pandas as pd


#
# Pandas functions
#
def read_tsv(file_path: str, **kwargs) -> pd.DataFrame:
    """
    Reads the given tab-separated file using Pandas.

    Args:
        file_path (str): The path to the tab-separated file.

    Returns:
        pd.DataFrame

    """
    return pd.read_csv(file_path, sep="\t", **kwargs)


def ordered_value_counts(series: pd.Series, name: Optional[str] = None) \
        -> pd.Series:
    """
    The equivalent of value_counts, but without relying on a hash table,
    which introduces inconsistent ordering. The effect of this is to maintain
    the original order of the series.

    https://github.com/pandas-dev/pandas/issues/12679

    """
    df = series.groupby(series, sort=False).count()
    return df if name is None else df.rename(name).reset_index()


def split_to_set(series: pd.Series, sep: str) -> pd.Series:
    """
    Splits a Series of string object type to a set.

    """
    return series.str.split(sep).map(set)


#
# Other functions
#
def dir_exists(dir_path: str) -> bool:
    """
    Tests whether the path provided corresponds to an existing directory.

    """
    return os.path.exists(dir_path) and os.path.isdir(dir_path)


def get_file_id(file_path: str) -> str:
    """
    Generates an 8-character file ID from the file path.

    """
    return os.path.basename(file_path)[:8]


def reversed_enumerate(sequence: Sequence):
    """
    Performs a reversed enumeration of the given sequence.

    """
    return reversed(list(enumerate(sequence)))
