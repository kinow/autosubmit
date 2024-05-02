#!/usr/bin/env python3

# Copyright 2014 Climate Forecasting Unit, IC3

# This file is part of Autosubmit.

# Autosubmit is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Autosubmit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Autosubmit.  If not, see <http://www.gnu.org/licenses/>.

from os import path
from setuptools import setup
from setuptools import find_packages

here = path.abspath(path.dirname(__file__))

# Get the version number from the relevant file
with open(path.join(here, 'VERSION')) as f:
    version = f.read().strip()

setup(
    name='autosubmit',
    license='GNU GPL v3',
    platforms=['GNU/Linux Debian'],
    version=version,
    description='Autosubmit is a Python-based workflow manager to create, manage and monitor complex tasks involving different substeps, such as scientific computational experiments. These workflows may involve multiple computing systems for their completion, from HPCs to post-processing clusters or workstations. Autosubmit can orchestrate all the tasks integrating the workflow by managing their dependencies, interfacing with all the platforms involved, and handling eventual errors.',
    long_description=open('README_PIP.md').read(),
    author='Daniel Beltran Mora',
    author_email='daniel.beltran@bsc.es',
    url='http://www.bsc.es/projects/earthscience/autosubmit/',
    download_url='https://earth.bsc.es/wiki/doku.php?id=tools:autosubmit',
    keywords=['climate', 'weather', 'workflow', 'HPC'],
    install_requires=[
        'zipp>=3.1.0',
        'cython',
        'autosubmitconfigparser==1.0.61',
        'paramiko>=3.4',
        'bcrypt>=3.2',
        'PyNaCl>=1.5.0',
        'configobj>=5.0.6',
        'python-dateutil>=2.8.2',
        'py3dotplus>=1.1.0',
        'pyparsing>=3.0.7',
        'mock>=4.0.3',
        'portalocker<=2.7.0',
        'networkx==2.6.3',
        'requests>=2.27.1',

        'bscearth.utils==0.5.2',
        'cryptography>=36.0.1',
        'xlib>=0.21',
        'ruamel.yaml==0.17.21',
        'pythondialog',
        'pytest',
        'nose',
        'coverage',
        'Pygments',
        'packaging==23',
        'wheel',
        'psutil',
        'rocrate==0.*'
    ],
    extras_require={
        ':python_version == "3.7"':
            [
                'rocrate==0.*',
                'PyNaCl==1.5.0',
                'pythondialog==3.5.3',
                'xlib==0.21',
                'setuptools==69.0.3',
                'cryptography==43.0.0.dev1',
                'bscearth.utils==0.5.2',
                'requests==2.31.0',
                'networkx==2.6.3',
                'portalocker==2.7.0',
                'mock==5.1.0',
                'paramiko==3.4.0',
                'pyparsing==3.1.1',
                'py3dotplus==1.1.0',
                'matplotlib==3.5.3',
                'python_dateutil==2.8.2',
                'argparse==1.4.0',
                'configobj==5.0.8',
                'packaging==23.2',
                'bcrypt==4.1.2',
                'ruamel.yaml==0.17.21',
                'zipp==3.17.0',
                'galaxy2cwl==0.1.4',
                'arcp==0.2.1',
                'charset_normalizer==3.3.2',
                'kiwisolver==1.4.5',
                'fonttools==4.47.2',
                'cycler==0.12.1',
                'ruamel.yaml.clib==0.2.8',
                'PyYAML==6.0.1',
                'gxformat2==0.18.0',
                'typing_extensions==4.9.0',
                'schema_salad==8.5.20240102191335',
                'bioblend==1.2.0',
                'rdflib==7.0.0',
                'mypy_extensions==1.0.0',
                'mistune==2.0.5',
                'importlib_resources==6.1.1',
                'cachecontrol==0.13.1',
                'tuspy==1.0.3',
                'isodate==0.6.1',
                'filelock==3.13.1',
            ],
        ':python_version > "3.7"':
            [
                'setuptools>60.11',
                'matplotlib<3.8.2',
                'six>=1.10.0',
                'pip>=22.0.3',
                'typing-extensions>=4',
            ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: POSIX :: Linux",
    ],
    packages=find_packages(),
    include_package_data=True,
    package_data={'autosubmit': [
        'autosubmit/config/files/autosubmit.conf',
        'autosubmit/config/files/expdef.conf',
        'autosubmit/database/data/autosubmit.sql',
        'README',
        'CHANGELOG',
        'VERSION',
        'LICENSE',
        'docs/autosubmit.pdf'
    ]
    },
    scripts=['bin/autosubmit']
)

