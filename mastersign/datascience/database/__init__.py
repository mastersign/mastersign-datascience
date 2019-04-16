# -*- coding: utf-8 -*-

"""
This module contains functionality to comfortably access a SQL database.
"""

import os
import pandas as pd
from sqlalchemy import create_engine
from ..files import read_parquet as read_cachefile
from ..files import write_parquet as write_cachefile

_def_db_conn = None


def set_default_db_conn(db_conn):
    """
    Sets the default connection string for subsequent database queries.

    :param db_conn: A SqlAlchemy connection string.
    """
    global _def_db_conn
    _def_db_conn = db_conn


def execute(sql, db_conn=None, *args, **kwargs):
    """
    Execute a SQL statement, returning no data.

    :param sql:     A string as a SQL statement.
    :param db_conn: A SqlAlchemy connection string. (optional)
    :param args:    Additional positional arguments,
                    passed to `sqlalchemy.engine.Connection.execute()`.
    :param kwargs:  Additional keyword arguments,
                    passed to `sqlalchemy.engine.Connection.execute()`.
    """
    engine = create_engine(db_conn or _def_db_conn)
    try:
        with engine.connect() as conn:
            conn.execute(sql, *args, **kwargs)
    finally:
        engine.dispose()


def load_query(query, db_conn=None,
               date=None, defaults=None, dtype=None, index=None,
               chunksize=4096, cachefile=None, compress_cache=False,
               **kwargs):
    """
    Load data from an arbitrary SQL query.

    :param query:   A string as a SQL query.
    :param db_conn: A SqlAlchemy connection string. (optional)
    :param date:    A column name or an iterable with column names,
                    or a dict with column names and date format strings,
                    for parsing specific columns as datetimes. (optional)
    :param defaults:
                    A dict with column names and default values for
                    `NULL` values. (optional)
                    Can be used to fill columns with defaults before converting
                    them to numeric data types with `dtype`.
                    See `pandas.DataFrame.fillna()` for more details.
    :param dtype:   A dict with column names and NumPy datatypes
                    or ``'category'``. (optional)
                    See `pandas.DataFrame.astype()` for details.
    :param index:   A column name or an iterable with column names,
                    which will be the index in the resulting DataFrame.
                    (optional)
    :param chunksize:
                    The number of rows to load in a chunk before
                    converting them into a Pandas DataFrame. (optional)
    :param cachefile:
                    A path to a file to cache the result data from the query.
                    (optional)
                    If the file already exists, the content of the file is returned
                    instead of connecting to the database.
    :param compress_cache:
                    A switch to activate data compression for the cache file.
    :param kwargs:  Additional keyword arguments
                    are passed to `pandas.read_sql_query()`.

    :return: Pandas DataFrame
    """
    if cachefile:
        if not os.path.isdir(os.path.dirname(cachefile)):
            raise FileNotFoundError("The parent directory for the cache file does not exist.")
        try:
            return read_cachefile(cachefile)
        except FileNotFoundError:
            pass

    if type(date) is str:
        date = (date,)

    def process_chunk(c):
        if defaults:
            c.fillna(defaults, inplace=True, downcast=dtype)
        if dtype:
            c = c.astype(dtype, copy=False)
        return c

    engine = create_engine(db_conn or _def_db_conn)
    try:
        with engine.connect().execution_options(stream_results=True) as conn:
            chunks = list(map(
                process_chunk,
                pd.read_sql_query(query, conn,
                                  index_col=index,
                                  parse_dates=date,
                                  chunksize=chunksize, **kwargs)))
    finally:
        engine.dispose()
    df = pd.concat(chunks)

    if cachefile:
        write_cachefile(df, cachefile, compress=compress_cache)

    return df


def load_scalar(query, db_conn=None, *args, **kwargs):
    """
    Load a single scalar from an arbitrary SQL query.


    :param query:   A string as a SQL query.
    :param db_conn: A SqlAlchemy connection string. (optional)
    :param args:    Additional positional arguments,
                    passed to `sqlalchemy.engine.Connection.execute()`.
    :param kwargs:  Additional keyword arguments,
                    passed to `sqlalchemy.engine.Connection.execute()`.

    :return: A single value
    """
    engine = create_engine(db_conn or _def_db_conn)
    try:
        with engine.connect().execution_options(stream_results=True) as conn:
            return conn.execute(query, *args, **kwargs).scalar()
    finally:
        engine.dispose()


def _select_query(table_name, columns=None, where=None, group_by=None, limit=None):
    if columns:
        column_list = ', '.join(columns)
    else:
        column_list = '*'

    if type(where) is str:
        where_clause = where
    elif where:
        where_clause = ' AND '.join(
            map(lambda term: term if type(term) is str else '(' + ' OR '.join(term) + ')',
                where))
    else:
        where_clause = ''
    if where_clause:
        where_clause = ' WHERE ' + where_clause

    if type(group_by) is str:
        group_by_clause = group_by
    elif group_by:
        group_by_clause = ', '.join(group_by)
    else:
        group_by_clause = ''
    if group_by_clause:
        group_by_clause = ' GROUP BY ' + group_by_clause

    if limit:
        limit_clause = ' LIMIT ' + str(int(limit))
    else:
        limit_clause = ''

    return "SELECT {} FROM `{}`{}{}{} ;".format(
        column_list, table_name, where_clause, group_by_clause, limit_clause)


def load_table(name, columns=None, where=None, group_by=None, limit=None,
               db_conn=None, date=None, defaults=None, dtype=None, index=None,
               chunksize=4096, cachefile=None, compress_cache=False,
               **kwargs):
    """
    Load data from a SQL table.

    :param name:     The name of the table.
    :param columns:  An iterable of column names. (optional)
    :param where:    A string with on condition or an iterable. (optional)
                     The iterable forms a conjunction and can hold strings
                     as conditions or nested iterables. The nested iterables
                     form disjunctions and must hold strings with conditions.
    :param group_by: A string as a GROUP-BY-clause or an iterable with
                     multiple GROUP-BY-clauses. (optional)
    :param limit:    The maximum number of rows to fetch. (optional)
    :param db_conn:  A SqlAlchemy connection string. (optional)
    :param date:     A column name or an iterable with column names,
                     or a dict with column names and date format strings,
                     for parsing specific columns as datetimes. (optional)
    :param defaults: A dict with column names and default values for
                     `NULL` values. (optional)
                     Can be used to fill columns with defaults before converting
                     them to numeric data types with `dtype`.
                     See `pandas.DataFrame.fillna()` for more details.
    :param dtype:    A dict with column names and NumPy datatypes
                     or ``'category'``. (optional)
                     See `pandas.DataFrame.astype()` for more details.
    :param index:    A column name or an iterable with column names,
                     which will be the index in the resulting DataFrame.
                     (optional)
    :param chunksize:
                     The number of rows to load in a chunk before
                     converting them into a Pandas DataFrame. (optional)
    :param cachefile:
                     A path to a file to cache the result data from the query.
                     (optional)
                     If the file already exists, the content of the file is returned
                     instead of connecting to the database.
    :param compress_cache:
                     A switch to activate data compression for the cache file.
    :param kwargs:   Additional keyword arguments
                     are passed to `pandas.read_sql_query()`.

    :return: Pandas DataFrame
    """
    sql_query = _select_query(name,
                              columns=columns, where=where,
                              group_by=group_by, limit=limit)
    return load_query(sql_query, db_conn=db_conn,
                      date=date, defaults=defaults, dtype=dtype, index=index,
                      chunksize=chunksize, cachefile=cachefile,
                      compress_cache=compress_cache, **kwargs)
