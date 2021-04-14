How to generate cmd files
#########################
To generate  the cmd files of the current non-active jobs experiment, it is possible to use the command:
::

    autosubmit inspect EXPID

EXPID is the experiment identifier.

Usage
=======
Options:
::

    usage: autosubmit inspect [-h]  [-fl] [-fc] [-fs] [-ft]  [-cw] expid

      expid                 experiment identifier

      -h, --help            show this help message and exit

      -fl FILTER_LIST, --list
                            List of job names to be generated
      -fc FILTER_CHUNK, --filter_chunk
                            List of chunks to be generated
      -fs FILTER_STATUS, --filter_status
                            List of status to be generated
      -ft FILTER_TYPE, --filter_type
                            List of types to be generated

      -cw                   --checkwrapper
                                Generate the wrapper cmd with the current filtered jobs

      -f                    --force
                                Generate all cmd files

Example
=======

with autosubmit.lock present or not:
::

    autosubmit inspect expid

with autosubmit.lock present or not:
::

    autosubmit inspect expid -f

without autosubmit.lock:
::

    autosubmit inspect expid -fl [-fc,-fs or ft]

To generate cmd for wrappers:
::

    autosubmit inspect expid -cw -f


With autosubmit.lock and no (-f) force, it will only generate all files that are not submitted.

Without autosubmit.lock, it will generate all unless filtered by -fl,fc,fs or ft.


