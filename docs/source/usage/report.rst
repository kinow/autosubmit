.. _report:

How to extract information about the experiment parameters
================================================

This procedure allows you to extract the experiment variables that you want.


The command can be called with:
::

    autosubmit report EXPID -t "absolute_file_path"

Alternatively it also can be called as follows:
::

    autosubmit report expid -all

Or combined as follows:
::

    autosubmit report expid -all -t "absolute_file_path"

Options:
::
    usage: autosubmit report [-all] [-t] [-fp] expid

        expid                                Experiment identifier

        -t, --template <path_to_template>    Allows to select a set of parameters to be extracted

        -fp, --show_all_parameters           All parameters will be extracted to a different file

        -fp, --folder_path                   By default, all parameters will be put into experiment tmp folder

Template format and example:
::
Autosubmit parameters are encapsulated by %_%, once you know how the parameter is called you can create a template similar to the one as follows:

- **CHUNKS:** %NUMCHUNKS% - %CHUNKSIZE% %CHUNKSIZEUNIT%
- **VERSION:** %VERSION%
- **MODEL_RES:** %MODEL_RES%
- **PROCS:** %XIO_NUMPROC% / %NEM_NUMPROC% / %IFS_NUMPROC% / %LPJG_NUMPROC% / %TM5_NUMPROC_X% / %TM5_NUMPROC_Y%
- **PRODUCTION_EXP:** %PRODUCTION_EXP%
- **OUTCLASS:** %BSC_OUTCLASS% / %CMIP6_OUTCLASS%

This will be understood by Autosubmit and the result would be similar to:

    CHUNKS: 2 - 1 month
    VERSION: trunk
    MODEL_RES: LR
    PROCS: 96 / 336 / - / - / 1 / 45
    PRODUCTION_EXP: FALSE
    OUTCLASS: reduced /  -

Although it depends on the experiment.

If the parameter doesn't exists, it will be returned as '-' while if the parameter is declared but empty it will remain empty

List of all parameters example:
::

On the other hand, if you use the option -l autosubmit will write a file called parameter_list_<todaydate>.txt containing all parameters in the format as follows:

HPCQUEUE=bsc_es
HPCARCH=marenostrum4
LOCAL_TEMP_DIR=/home/dbeltran/experiments/ASlogs
NUMCHUNKS=1
PROJECT_ORIGIN=https://earth.bsc.es/gitlab/es/auto-ecearth3.git
MARENOSTRUM4_HOST=mn1.bsc.es
NORD3_QUEUE=bsc_es
NORD3_ARCH=nord3
CHUNKSIZEUNIT=month
MARENOSTRUM4_LOGDIR=/gpfs/scratch/bsc32/bsc32070/a01w/LOG_a01w
PROJECT_COMMIT=
SCRATCH_DIR=/gpfs/scratch
HPCPROJ=bsc32
NORD3_BUDG=bsc32
