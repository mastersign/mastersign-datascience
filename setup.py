#!/usr/bin/env python

import os
from setuptools import setup, find_namespace_packages

import mastersign.datascience.core as root


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


info_files = ['README', 'LICENSE']
info_texts = read_info_files(*info_files)

long_description = """
{README}
""".format(**info_texts)

data_files = None

setup(
    name='mastersign-datascience',
    version=root.__version__,
    description=root.__doc__.strip().replace('\n', ' '),
    long_description=long_description,
    keywords=' '.join(root.__keywords__),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    url=root.__url__,
    author=root.__author__,
    author_email=root.__author_email__,
    maintainer=root.__maintainer__,
    maintainer_email=root.__maintainer_email__,
    license='BSD-3',
    packages=find_namespace_packages(include=['mastersign.*']),
    data_files=data_files,
    install_requires=read_dependencies(),
)
