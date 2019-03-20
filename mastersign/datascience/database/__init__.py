# -*- coding: utf-8 -*-

"""
This module contains functionality to comfortably access a SQL database.
"""

import pandas as pd
from sqlalchemy import create_engine

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

    :param query:  A string as a SQL statement.
    :param dbconn: A SqlAlchemy connection string. (optional)
    :param args:   Additional positional arguments,
                   passed to `sqlalchemy.engine.Connection.execute()`.
    :param kwargs: Additional keyword arguments,
                   passed to `sqlalchemy.engine.Connection.execute()`.
    """
    engine = create_engine(db_conn or _def_db_conn)
    try:
        with engine.connect() as connection:
            connection.execute(sql, *args, **kwargs)
    finally:
        engine.dispose()


def load_query(query, db_conn=None, **kwargs):
    """
    Load data from an arbitrary SQL query.

    :param query:   A string as a SQL query.
    :param db_conn: A SqlAlchemy connection string. (optional)
    :param kwargs:  Additional keyword arguments
                    are passed to `pandas.read_sql_query()`.

    :return: Pandas DataFrame
    """
    return pd.read_sql_query(query, db_conn or _def_db_conn, **kwargs)


def _select_query(table_name, columns=None, where=None, group_by=None):
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

    return "SELECT {} FROM `{}`{}{} ;".format(
        column_list, table_name, where_clause, group_by_clause)


def load_table(name, columns=None, where=None, group_by=None, db_conn=None, **kwargs):
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
    :param db_conn:  A SqlAlchemy connection string. (optional)
    :param kwargs:   Additional keyword arguments
                     are passed to `pandas.read_sql_query()`.

    :return: Pandas DataFrame
    """
    return load_query(_select_query(name, columns=columns, where=where, group_by=group_by), db_conn=db_conn, **kwargs)
