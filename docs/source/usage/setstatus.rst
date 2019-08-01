How to change job status
==========================
To change the status of one or more jobs, it is possible to use the command:
::

    autosubmit setstatus EXPID

EXPID is the experiment identifier.

Options:
::

    usage: autosubmit setstatus [-h] [-np] [-s] [-t] [-o {pdf,png,ps,svg}] [-fl] [-fc] [-fs] [-ft] [-group_by {date,member,chunk,split} -expand -expand_status] [-cw] expid

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
      -ftc FILTER_TYPE_CHUNK --filter_type_chunk 
                            Accepts a string with the formula: "[ 19601101 [ fc0 [1 2 3 4] Any [1] ] 19651101 [ fc0 [16 30] ] ],SIM,SIM2"
                            Where SIM, SIM2 are section (or job type) names that also accept the keyword "Any" so the changes apply to all sections.
                            Starting Date (19601101) does not accept the keyword "Any".
                            Member names (fc0) accept the keyword "Any", so the chunks ([1 2 3 4]) given will be updated in all members.
                            Chunks must be in the format "[1 2 3 4 n]" where "n" is an integer representing the number of the chunk in the member, 
                            no range format is allowed.
      -d                    When using the option -ftc and sending this flag, a tree view of the experiment with markers indicating which jobs
                            have been changed will be generated. 
      --hide,               hide the plot
      -group_by {date,member,chunk,split,automatic}
                            criteria to use for grouping jobs
      -expand,              list of dates/members/chunks to expand
      -expand_status,       status(es) to expand
      -nt                   --notransitive
                                prevents doing the transitive reduction when plotting the workflow
      -cw                   --check_wrapper
                                Generate the wrapper in the current workflow

Example:
::

    autosubmit setstatus cxxx

In order to understand more the grouping options, which are used for visualization purposes, please check :ref:`grouping`.
