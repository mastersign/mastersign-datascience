#!/usr/bin/env python

import os
from setuptools import setup, find_packages

import mastersign


def read_info_files(*names):
    values = dict()
    for name in names:
        value = ''
        for extension in ('.txt', '.rst'):
            filename = name + extension
            if os.path.isfile(filename):
                with open(filename) as fd:
                    value = fd.read()
                break
        values[name] = value
    return values


def read_dependencies():
    requirements_file = 'requirements.txt'
    if os.path.isfile(requirements_file):
        with open(requirements_file) as fd:
            return [l.strip() for l in fd.readlines()]
    return None


info_files = ['README', 'CHANGELOG', 'LICENSE']
info_texts = read_info_files(*info_files)

long_description = """
{README}

{CHANGELOG}
""".format(**info_texts)

data_files = None

setup(
    name='mastersign-datascience',
    version=mastersign.__version__,
    description=mastersign.__doc__.strip().replace('\n', ' '),
    long_description=long_description,
    keywords=' '.join(mastersign.__keywords__),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    url=mastersign.__url__,
    author=mastersign.__author__,
    author_email=mastersign.__author_email__,
    maintainer=mastersign.__maintainer__,
    maintainer_email=mastersign.__maintainer_email__,
    license='BSD-3',
    packages=find_packages(),
    data_files=data_files,
    install_requires=read_dependencies(),
)
