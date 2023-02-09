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
    install_requires=['autosubmitconfigparser==0.0.77','packaging>19','six>=1.10.0','configobj>=5.0.6','argparse>=1.4.0','python-dateutil>=2.8.2','matplotlib>=3.4.3','numpy<1.22','py3dotplus>=1.1.0','pyparsing>=3.0.7','paramiko>=2.9.2','mock>=4.0.3','portalocker>=2.3.2','networkx==2.6.3','requests>=2.27.1','bscearth.utils>=0.5.2','cryptography>=36.0.1','setuptools>=60.8.2','xlib>=0.21','pip>=22.0.3','ruamel.yaml','pythondialog','pytest','nose','coverage','PyNaCl>=1.4.0','Pygments'],
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
