How to change job status
==========================
To change the status of one or more jobs, it is possible to use the command:
::

    autosubmit setstatus EXPID

EXPID is the experiment identifier.

Options:
::

    usage: autosubmit setstatus [-h] [-np] [-s] [-t] [-o {pdf,png,ps,svg}] [-fl] [-fc] [-fs] [-ft] [-group_by {date,member,chunk,split} -expand -expand_status] expid

      expid                 experiment identifier

      -h, --help            show this help message and exit
      -o {pdf,png,ps,svg}, --output {pdf,png,ps,svg}
                            type of output for generated plot
      -np, --noplot         omit plot
      -s, --save            Save changes to disk
      -t, --status_final    Target status
      -fl FILTER_LIST, --list
                            List of job names to be changed
      -fc FILTER_CHUNK, --filter_chunk
                            List of chunks to be changed
      -fs FILTER_STATUS, --filter_status
                            List of status to be changed
      -ft FILTER_TYPE, --filter_type
                            List of types to be changed
      --hide,               hide the plot
      -group_by {date,member,chunk,split,automatic}
                            criteria to use for grouping jobs
      -expand,              list of dates/members/chunks to expand
      -expand_status,       status(es) to expand

Example:
::

    autosubmit setstatus cxxx

In order to understand more the grouping options, which are used for visualization purposes, please check :ref:`grouping`.
