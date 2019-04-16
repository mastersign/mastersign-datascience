# -*- coding: utf-8 -*-

"""
This module contains functionality to read and write Pandas DataFrames
from and to files.
"""

import pandas as pd
from fastparquet import write, ParquetFile


def read_parquet(filename, columns=None, index=None):
    """
    Read the content of a Parquet file into a Pandas DataFrame.

    :param filename: A path to a Parquet file.
    :param columns:  A list of column names to load. (optional)
                     If `None` is given, all columns from the file are read.
    :param index:    A column name or a list of column names,
                     which should be used as the index for resulting
                     DataFrame. (optional)
                     By default, the index columns marked in the metadata
                     of the file are used as index for the DataFrame.
                     If no colums are marked as index, a simple incremental
                     integer index is created.
    :return: A Pandas DataFrame.
    """
    pf = ParquetFile(filename)
    return pf.to_pandas(columns=columns, index=index)


def write_parquet(data: pd.DataFrame, filename, compress=False, append=False):
    """
    Write a Pandas DataFrame into a Parquet file.

    :param data:     A Pandas DataFrame.
    :param filename: A path to the target Parquet file.
                     If the file already exists and `append` is `False`,
                     it is overwritten.
    :param compress: A switch to activate GZIP compression. (optional)
    :param append:   A switch to append the DataFrame to the file,
                     incase it already exists. (optional)
                     The schema of the DataFrame must match the existing data
                     in the file.
    """
    write(filename, data, compression=('GZIP' if compress else None), append=append)
