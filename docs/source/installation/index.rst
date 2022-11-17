############
Installation
############

How to install
==============

The Autosubmit code is maintained in *PyPi*, the main source for python packages.

- Pre-requisites: bash, python3, sqlite3, git-scm > 1.8.2, subversion, dialog, curl, python-tk(tkinter in centOS), graphviz >= 2.41, pip3

.. important:: (SYSTEM) Graphviz version must be >= 2.38 except 2.40(not working). You can check the version using dot -v.

- Python dependencies: configobj>=5.0.6, argparse>=1.4.0 , python-dateutil>=2.8.2, matplotlib==3.4.3, numpy==1.21.6, py3dotplus>=1.1.0, pyparsing>=3.0.7, paramiko>=2.9.2, mock>=4.0.3, six>=1.10,  portalocker>=2.3.2, networkx==2.6.3, requests>=2.27.1, bscearth.utils>=0.5.2, cryptography>=36.0.1, setuptools>=60.8.2, xlib>=0.21, pip>=22.0.3, ruamel.yaml, pythondialog, pytest, nose, coverage, PyNaCl==1.4.0, six>=1.10.0, requests, xlib, Pygments, packaging==19, typing>=3.7, autosubmitconfigparser

.. important:: dot -v command should contain "dot",pdf,png,svg,xlib  in device section.

.. important:: The host machine has to be able to access HPC's/Clusters via password-less ssh. Make sure that the ssh key is in PEM format `ssh-keygen -t rsa -b 4096 -C "email@email.com" -m PEM`.


To install autosubmit just execute:
::

    pip install autosubmit

or download, unpack and:
::

    python3 setup.py install

.. hint::
    To check if autosubmit has been installed run ``autosubmit -v.`` This command will print autosubmit's current
    version

.. hint::
    To read autosubmit's readme file, run ``autosubmit readme``

.. hint::
    To see the changelog, use ``autosubmit changelog``

How to configure
================

After installation, you have to configure database and path for Autosubmit.
In order to use the default settings, just create a directory called `autosubmit` in your home directory before running the configure command.
The experiments will be created in this folder, and the database named `autosubmit.db` in your home directory.

::

    autosubmit configure




For advanced options you can add ``--advanced`` to the configure command. It will allow you to choose different directories (they must exist) for the experiments and database,
as well as configure SMTP server and an email account in order to use the email notifications feature.


::

    autosubmit configure --advanced


.. hint::
    The ``dialog`` (GUI) library is optional. Otherwise the configuration parameters
    will be prompted (CLI). Use ``autosubmit configure -h`` to see all the allowed options.


For installing the database for Autosubmit on the configured folder, when no database is created on the given path, execute:
::

    autosubmit install

.. danger:: Be careful ! autosubmit install will create a blank database.

Lastly, if autosubmit configure doesn't work for you or you need to configure additional info create:

Create or modify /etc/autosubmitrc file or ~/.autosubmitrc with the information as follows:

.. code-block:: ini

    [database]
    path = path to autosubmit db
    filename = autosubmit.db

    [local]
    path = path to experiment folders

    [conf]
    jobs = path to any experiment  jobs conf # If not working on esarchive, you must create one from scratch check the how to.
    platforms = path to any experiment  platform conf # If not working on esarchive, you must create one from scratch check the how to.

    [mail]
    smtp_server = mail.bsc.es
    mail_from = automail@bsc.es

    [structures]
    path =  path to experiment folders

    [globallogs]
    path =  path to global logs (for expid,delete and migrate commands)

    [historicdb]
    path = <experiment_folder>/historic

    [autosubmitapi]
    url = url of Autosubmit API (The API is provided inside the BSC network) 
    # Autosubmit API provides extra information for some Autosubmit functions. It is not mandatory to have access to it to use Autosubmit.

    [hosts]
    authorized = [run bscearth000,bscesautosubmit01,bscesautosubmit02] [stats,clean,describe,check,report,dbfix,pklfix,updatedescript,updateversion all]
    forbidden = [expìd,create,recovery,delete,inspect,monitor,recovery,migrate,configure,setstatus,testcase,test,refresh,archive,unarchive bscearth000,bscesautosubmit01,bscesautosubmit02]


Hosts:
From 3.14+ onwards, autosubmit commands can be tailored to run on specific machines. Previously, only run was affected by the deprecated whitelist parameter.
 * authorized: [<command1,commandN> <machine1,machineN>] list of machines that can run given autosubmit commands.
 * forbidden:  [<command1,commandN> <machine1,machineN>] list of machines that cannot run given autosubmit commands.
 * If no commands are defined, all commands are authorized.
 * If no machines are defined, all machines are authorized.

Now you are ready to use Autosubmit !


Examples
========

Sequence of instructions to install Autosubmit and its dependencies in Ubuntu.
------------------------------------------------------------------------------

.. code-block:: bash


    # Update repositories
    apt update

    # Avoid interactive stuff
    export DEBIAN_FRONTEND=noninteractive

    # Dependencies
    apt install wget curl python3 python3-tk python3-dev graphviz -y -q

    # Additional dependencies related with pycrypto
    apt install build-essential libssl-dev libffi-dev -y -q

    # Install autosubmit using pip
    pip3 install autosubmit

    # Check that we can execute autosubmit commands
    autosubmit -h

    # Configure
    autosubmit configure

    # Install
    autosubmit install

    # Get expid
    autosubmit expid -H "local" -d "Test exp in local"

    # Create with
    # Since it was a new install the expid will be a000
    autosubmit create a000

    # run
    autosubmit run a000
Sequence of instructions to install Autosubmit and its dependencies with conda.
-------------------------------------------------------------------------------

.. code-block:: bash

    # Download conda
    wget https://repo.anaconda.com/miniconda/Miniconda3-py39_4.12.0-Linux-x86_64.sh
    # Launch it
    chmod +x ./Miniconda3-py39_4.12.0-Linux-x86_64.sh ; ./Miniconda3-py39_4.12.0-Linux-x86_64.sh
    # Download git
    apt install git -y -q
    # Download autosubmit
    git clone https://earth.bsc.es/gitlab/es/autosubmit.git -b v4.0.0b
    cd autosubmit
    # Create conda environment
    conda env update -f environment.yml -n autosubmit python=3.7
    # Activate env
    conda activate autosubmit
    # Test autosubmit
    autosubmit -v
    # Configure autosubmitrc and install the database as indicated in the installation instructions above this section

.. hint::
    After installing conda, you may need to close the terminal and re-open it so the installation takes effect.