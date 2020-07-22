How to create a test case experiment
====================================
This method is to create a test case experiment. It creates a new experiment for a test case with a
given number of chunks, start date, member and HPC.

To create a test case experiment, use the command:
::

    autosubmit testcase



Options:
::

    usage: autosubmit testcase [-h] [-y COPY] -d DESCRIPTION [-c CHUNKS]
                               [-m MEMBER] [-s STARDATE] [-H HPC] [-b BRANCH]

        expid                 experiment identifier

         -h, --help            show this help message and exit
         -c CHUNKS, --chunks CHUNKS
                               chunks to run
         -m MEMBER, --member MEMBER
                               member to run
         -s STARDATE, --stardate STARDATE
                               stardate to run
         -H HPC, --HPC HPC     HPC to run experiment on it
         -b BRANCH, --branch BRANCH
                               branch from git to run (or revision from subversion)

Example:
::

    autosubmit testcase -d "TEST CASE cca-intel auto-ecearth3 layer 0: T511L91-ORCA025L75-LIM3 (cold restart) (a092-a09n)" -H cca-intel -b 3.2.0b_develop -y a09n

