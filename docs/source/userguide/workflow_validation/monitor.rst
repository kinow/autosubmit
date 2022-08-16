How to monitor the experiment
=============================
To monitor the status of the experiment, use the command:
::

    autosubmit monitor EXPID

*EXPID* is the experiment identifier.

Options:
::

    usage: autosubmit monitor [-h] [-o {pdf,png,ps,svg,txt}] [-group_by {date,member,chunk,split} -expand -expand_status] [-fl] [-fc] [-fs] [-ft] [-cw] expid [-txt] [-txtlog]

      expid                 Experiment identifier.

      -h, --help            Show this help message and exit.
      -o {pdf,png,ps,svg}, --output {pdf,png,ps,svg,txt}
                            Type of output for generated plot (or text file).
      -group_by {date,member,chunk,split,automatic}
                            Criteria to use for grouping jobs.
      -expand,              List of dates/members/chunks to expand.
      -expand_status,       Status(es) to expand.
      -fl FILTER_LIST, --list
                            List of job names to be filtered.
      -fc FILTER_CHUNK, --filter_chunk
                            List of chunks to be filtered.
      -fs FILTER_STATUS, --filter_status
                            Status to be filtered.
      -ft FILTER_TYPE, --filter_type
                            Type to be filtered.
      --hide,               Hide the plot.
      -txt, --text          
                            Generates a tree view format that includes job name, children number, and status in a file in the /status/ folder. If possible, shows the results in the terminal.                            
      -txtlog, --txt_logfiles  
                            Generates a list of job names, status, .out path, and .err path as a file in /status/ (AS <3.12 behaviour).
      -nt                   --notransitive
                                Prevents doing the transitive reduction when plotting the workflow.
      -cw                   --check_wrapper
                                Generate the wrapper in the current workflow.
                                
Example:
::

    autosubmit monitor cxxx

The location where the user can find the generated plots with date and timestamp can be found below:

::

    <experiments_directory>/cxxx/plot/cxxx_<date>_<time>.pdf

The location where the user can find the txt output containing the status of each job and the path to out and err log files.

::

    <experiments_directory>/cxxx/status/cxxx_<date>_<time>.txt

.. hint::
    Very large plots may be a problem for some pdf and image viewers.
    If you are having trouble with your usual monitoring tool, try using svg output and opening it with Google Chrome with the SVG Navigator extension installed.

In order to understand more the grouping options, please check :ref:`grouping`.