# -*- coding: utf-8 -*-

"""
High level helpers for data science in Python with Pandas.
"""

import logging


try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())


# package metadata

__version__ = '0.1.0'
__url__ = 'https://github.com/mastersign/mastersign-datascience.git'
__author__ = 'Tobias Kiertscher'
__author_email__ = 'dev@mastersign.de'
__maintainer__ = 'Tobias Kiertscher'
__maintainer_email__ = 'dev@mastersign.de'
__keywords__ = ['lib', 'datascience']
