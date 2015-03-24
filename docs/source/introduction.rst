************
Introduction
************

Autosubmit is a tool to create, manage and monitor experiments by using Computing Clusters, HPC's and Supercomputers
remotely via ssh. It has support for experiments running in more than one HPC and for different workflow configurations.


For help about how to use autosubmit and a list of available commands execute

::

    autosubmit -h

    usage: autosubmit [-h] [-v]
                  [-lf {EVERYTHING,DEBUG,INFO,RESULT,USER_WARNING,WARNING,ERROR,CRITICAL,NO_LOG}]
                  [-lc {EVERYTHING,DEBUG,INFO,RESULT,USER_WARNING,WARNING,ERROR,CRITICAL,NO_LOG}]

                  {run,expid,delete,monitor,stats,clean,recovery,check,create,configure,install,change_pkl,test,refresh}
                  ...

    Main executable for autosubmit.

    positional arguments:
      {run,expid,delete,monitor,stats,clean,recovery,check,create,configure,install,change_pkl,test,refresh}

    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         returns autosubmit's version number and exit
      -lf {EVERYTHING,DEBUG,INFO,RESULT,USER_WARNING,WARNING,ERROR,CRITICAL,NO_LOG}, --logfile {EVERYTHING,DEBUG,INFO,RESULT,USER_WARNING,WARNING,ERROR,CRITICAL,NO_LOG}
                            sets file's log level.
      -lc {EVERYTHING,DEBUG,INFO,RESULT,USER_WARNING,WARNING,ERROR,CRITICAL,NO_LOG}, --logconsole {EVERYTHING,DEBUG,INFO,RESULT,USER_WARNING,WARNING,ERROR,CRITICAL,NO_LOG}
                            sets console's log level

Execute autosubmit <command> -h for detailed help for each command