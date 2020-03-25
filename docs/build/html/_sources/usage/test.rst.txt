How to test the experiment
==========================
This method is to conduct a test for a given experiment. It creates a new experiment for a given experiment with a
given number of chunks with a random start date and a random member to be run on a random HPC.

To test the experiment, use the command:
::

    autosubmit test CHUNKS EXPID

*EXPID* is the experiment identifier.
*CHUNKS* is the number of chunks to run in the test.



Options:
::

    usage: autosubmit test [-h] -c CHUNKS [-m MEMBER] [-s STARDATE] [-H HPC] [-b BRANCH] expid

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

    autosubmit test -c 1 -s 19801101 -m fc0 -H ithaca -b develop cxxx