########
Tutorial
########

Quick start guide
=================

First Step: Experiment creation
-------------------------------

To create a new experiment, run the command:
::

    autosubmit expid -H HPCname -d Description

*HPCname* is the name of the main HPC platform for the experiment: it will be the default platform for the tasks.
*Description* is a brief experiment description.

This command assigns a unique four character identifier (``xxxx``, names starting from a letter, the other three characters) to the experiment and creates a new folder in experiments repository.

Examples:
::

    autosubmit expid --HPC ithaca --description "experiment is about..."

.. caution:: The *HPCname*, e.g. ithaca, must be defined in the platforms configuration.
    See next section :ref:`confexp`.

::

    autosubmit expid --copy a000 --HPC ithaca -d "experiment is about..."

.. warning:: You can only copy experiments created with Autosubmit 3.0 or above.

.. _confexp:

Second Step: Experiment configuration
-------------------------------------

To configure the experiment, edit ``expdef_cxxx.conf``, ``jobs_cxxx.conf`` and ``platforms_cxxx.conf`` in the ``conf`` folder of the experiment.

*expdef_cxxx.conf* contains:
    - Start dates, members and chunks (number and length).
    - Experiment project source: origin (version control system or path)
    - Project configuration file path.

*jobs_cxxx.conf* contains the workflow to be run:
    - Scripts to execute.
    - Dependencies between tasks.
    - Task requirements (processors, wallclock time...).
    - Platform to use.

*platforms_cxxx.conf* contains:
    - HPC, fat-nodes and supporting computers configuration.

.. note:: *platforms_cxxx.conf* is usually provided by technicians, users will only have to change login and accounting options for HPCs.

.. note::
    There are multiple implementations of the communication with the platforms, so if you are interested in changing
    the default implementation, you can see how to do it on the 'Usage' section.

You may want to configure Autosubmit parameters for the experiment. Just edit ``autosubmit_cxxx.conf``.

*autosubmit_cxxx.conf* contains:
    - Maximum number of jobs to be waiting in the HPC queue.
    - Maximum number of jobs to be running at the same time at the HPC.
    - Time (seconds) between connections to the HPC queue scheduler to poll already submitted jobs status.
    - Number of retrials if a job fails.
    - Default output type for some Autosubmit functions

Examples:
::

    vi <experiments_directory>/cxxx/conf/expdef_cxxx.conf

.. code-block:: ini

    [DEFAULT]
    # Experiment identifier
    # No need to change
    EXPID = cxxx
    # HPC name.
    # No need to change
    HPCARCH = ithaca

    [experiment]
    # Supply the list of start dates. Available formats: YYYYMMDD YYYYMMDDhh YYYYMMDDhhmm
    # Also you can use an abreviated sintax for multiple dates with common parts:
    # 200001[01 15] <=> 20000101 20000115
    # DATELIST = 19600101 19650101 19700101
    # DATELIST = 1960[0101 0201 0301]
    DATELIST = 19900101
    # Supply the list of members. LIST = fc0 fc1 fc2 fc3 fc4
    MEMBERS = fc0
    # Chunk size unit. STRING = hour, day, month, year
    CHUNKSIZEUNIT = month
    # Chunk size. NUMERIC = 4, 6, 12
    CHUNKSIZE = 1
    # Total number of chunks in experiment. NUMERIC = 30, 15, 10
    NUMCHUNKS = 2
    # Calendar used. LIST: standard, noleap
    CALENDAR = standard

    [rerun]
    # Is a rerun or not? [Default: Do set FALSE]. BOOLEAN = TRUE, FALSE
    RERUN = FALSE
    # If RERUN = TRUE then supply the list of chunks to rerun
    # LIST = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]"
    CHUNKLIST =

    [project]
    # Select project type. STRING = git, svn, local, none
    # If PROJECT_TYPE is set to none, Autosubmit self-contained dummy templates will be used
    PROJECT_TYPE = git
    # Destination folder name for project. type = STRING, default = leave empty,
    PROJECT_DESTINATION = model

    # If PROJECT_TYPE is not git, no need to change
    [git]
    # Repository URL  STRING = 'https://github.com/torvalds/linux.git'
    PROJECT_ORIGIN = https://gitlab.cfu.local/cfu/auto-ecearth3.git
    # Select branch or tag, STRING, default = 'master',
    # help = {'master' (default), 'develop', 'v3.1b', ...}
    PROJECT_BRANCH = develop
    # type = STRING, default = leave empty, help = if model branch is a TAG leave empty
    PROJECT_COMMIT =

    # If PROJECT_TYPE is not svn, no need to change
    [svn]
    # type = STRING, help = 'https://svn.ec-earth.org/ecearth3'
    PROJECT_URL =
    # Select revision number. NUMERIC = 1778
    PROJECT_REVISION =

    # If PROJECT_TYPE is not local, no need to change
    [local]
    # type = STRING, help = /foo/bar/ecearth
    PROJECT_PATH =

    # If PROJECT_TYPE is none, no need to change
    [project_files]
    # Where is PROJECT CONFIGURATION file location relative to project root path
    FILE_PROJECT_CONF = templates/ecearth3/ecearth3.conf
    # Where is JOBS CONFIGURATION file location relative to project root path
    FILE_JOBS_CONF = templates/common/jobs.conf

::

    vi <experiments_directory>/cxxx/conf/jobs_cxxx.conf

.. code-block:: ini

    # Example job with all options specified

    ## Job name
    # [JOBNAME]
    ## Script to execute. If not specified, job will be omited from workflow.
    ## Path relative to the project directory
    # FILE =
    ## Platform to execute the job. If not specificied, defaults to HPCARCH in expedf file.
    ## LOCAL is always defined and referes to current machine
    # PLATFORM =
    ## Queue to add the job to. If not specificied, uses PLATFORM default.
    # QUEUE =
    ## Defines dependencies from job as a list of parents jobs separed by spaces.
    ## Dependencies to jobs in previous chunk, member o startdate, use -(DISTANCE)
    # DEPENDENCIES = INI SIM-1 CLEAN-2
    ## Define if jobs runs once, once per stardate, once per member or once per chunk. Options: once, date, member, chunk.
    ## If not specified, defaults to once
    # RUNNING = once
    ## Specifies that job has only to be run after X dates, members or chunk. A job will always be created for the last
    ## If not specified, defaults to 1
    # FREQUENCY = 3
    ## On a job with FREQUENCY > 1, if True, the dependencies are evaluated against all
    ## jobs in the frequency interval, otherwise only evaluate dependencies against current
    ## iteration.
    ## If not specified, defaults to True
    # WAIT = False
    ## Defines if job is only to be executed in reruns. If not specified, defaults to false.
    # RERUN_ONLY = False
    ## Defines jobs needed to be rerun if this job is going to be rerun
    # RERUN_DEPENDENCIES = RERUN INI LOCAL_SETUP REMOTE_SETUP TRANSFER
    ## Wallclock to be submitted to the HPC queue in format HH:MM
    # WALLCLOCK = 00:05
    ## Processors number to be submitted to the HPC. If not specified, defaults to 1.
    # PROCESSORS = 1
    ## Threads number to be submitted to the HPC. If not specified, defaults to 1.
    # THREADS = 1
    ## Tasks number to be submitted to the HPC. If not specified, defaults to empty.
    # TASKS =
    ## Memory requirements for the job in MB
    # MEMORY = 4096
    ##  Number of retrials if a job fails. If not specified, defaults to the value given on experiment's autosubmit.conf
    # RETRIALS = 4
    ## Some jobs can not be checked before running previous jobs. Set this option to false if that is the case
    # CHECK = False
    ## Select the interpreter that will run the job. Options: bash, python, r Default: bash
    # TYPE = bash


    [LOCAL_SETUP]
    FILE = LOCAL_SETUP.sh
    PLATFORM = LOCAL

    [REMOTE_SETUP]
    FILE = REMOTE_SETUP.sh
    DEPENDENCIES = LOCAL_SETUP
    WALLCLOCK = 00:05

    [INI]
    FILE = INI.sh
    DEPENDENCIES = REMOTE_SETUP
    RUNNING = member
    WALLCLOCK = 00:05

    [SIM]
    FILE = SIM.sh
    DEPENDENCIES = INI SIM-1 CLEAN-2
    RUNNING = chunk
    WALLCLOCK = 00:05
    PROCESSORS = 2
    THREADS = 1
    TASKS = 1

    [POST]
    FILE = POST.sh
    DEPENDENCIES = SIM
    RUNNING = chunk
    WALLCLOCK = 00:05

    [CLEAN]
    FILE = CLEAN.sh
    DEPENDENCIES = POST
    RUNNING = chunk
    WALLCLOCK = 00:05

    [TRANSFER]
    FILE = TRANSFER.sh
    PLATFORM = LOCAL
    DEPENDENCIES = CLEAN
    RUNNING = member

::

    vi <experiments_directory>/cxxx/conf/platforms_cxxx.conf

.. code-block:: ini

    # Example platform with all options specified

    ## Platform name
    # [PLAFORM]
    ## Queue type. Options: PBS, SGE, PS, LSF, ecaccess, SLURM
    # TYPE =
    ## Version of queue manager to use. Needed only in PBS (options: 10, 11, 12) and ecaccess (options: pbs, loadleveler)
    # VERSION =
    ## Hostname of the HPC
    # HOST =
    ## Project for the machine scheduler
    # PROJECT =
    ## Budget account for the machine scheduler. If omitted, takes the value defined in PROJECT
    # BUDGET =
    ## Option to add project name to host. This is required for some HPCs
    # ADD_PROJECT_TO_HOST = False
    ## User for the machine scheduler
    # USER =
    ## Path to the scratch directory for the machine
    # SCRATCH_DIR = /scratch
    ## If true, autosubmit test command can use this queue as a main queue. Defaults to false
    # TEST_SUITE = False
    ## If given, autosubmit will add jobs to the given queue
    # QUEUE =
    ## If specified, autosubmit will run jobs with only one processor in the specified platform.
    # SERIAL_PLATFORM = SERIAL_PLATFORM_NAME
    ## If specified, autosubmit will run jobs with only one processor in the specified queue.
    ## Autosubmit will ignore this configuration if SERIAL_PLATFORM is provided
    # SERIAL_QUEUE = SERIAL_QUEUE_NAME
    ## Default number of processors per node to be used in jobs
    # PROCESSORS_PER_NODE =
    ## Default Maximum number of jobs to be waiting in any platform queue
    ## Default = 3
    # MAX_WAITING_JOBS = 3
    ## Default maximum number of jobs to be running at the same time at any platform
    ## Default = 6
    # TOTAL_JOBS = 6

    [ithaca]
    # Queue type. Options: ps, SGE, LSF, SLURM, PBS, eceaccess
    TYPE = SGE
    HOST = ithaca
    PROJECT = cfu
    ADD_PROJECT_TO_HOST = true
    USER = dmanubens
    SCRATCH_DIR = /scratch/cfu
    TEST_SUITE = True

::

    vi <experiments_directory>/cxxx/conf/autosubmit_cxxx.conf

.. code-block:: ini

    [config]
    # Experiment identifier
    # No need to change
    EXPID =
    # No need to change.
    # Autosubmit version identifier
    AUTOSUBMIT_VERSION =
    # Default maximum number of jobs to be waiting in any platform
    # Default = 3
    MAXWAITINGJOBS = 3
    # Default maximum number of jobs to be running at the same time at any platform
    # Default = 6
    TOTALJOBS = 6
    # Time (seconds) between connections to the HPC queue scheduler to poll already submitted jobs status
    # Default = 10
    SAFETYSLEEPTIME = 10
    # Number of retrials if a job fails. Can ve override at job level
    # Default = 0
    RETRIALS = 0
    # Default output type for CREATE, MONITOR, SET STATUS, RECOVERY. Available options: pdf, svg, png, ps, txt 
    # Default = pdf
    OUTPUT = pdf

Then, Autosubmit *create* command uses the ``expdef_cxxx.conf`` and generates the experiment:
::

    autosubmit create cxxx

*cxxx* is the name of the experiment.

In the process of creating the new experiment a plot has been created.

It can be found in ``<experiments_directory>/cxxx/plot/``

Third Step: Experiment run
--------------------------

After filling the experiment configuration and create, user can go into ``proj`` which has a copy of the model.

A short reference on how to prepare the experiment project is detailed in the following section of this documentation:

:doc:`project`

The experiment project contains the scripts specified in ``jobs_xxxx.conf`` and a copy of model source code and data specified in ``expdef_xxxx.conf``.

To configure experiment project parameters for the experiment, edit ``proj_cxxx.conf``.

*proj_cxxx.conf* contains:
    - The project dependant experiment variables that Autosubmit will substitute in the scripts to be run.

.. warning:: The ``proj_xxxx.conf`` has to be defined in INI style so it should has section headers. At least one.

Example:
::

    vi <experiments_directory>/cxxx/conf/proj_cxxx.conf

.. code-block:: ini

    [common]
    # No need to change.
    MODEL = ecearth
    # No need to change.
    VERSION = v3.1
    # No need to change.
    TEMPLATE_NAME = ecearth3
    # Select the model output control class. STRING = Option
    # listed under the section : https://earth.bsc.es/wiki/doku.php?id=overview_outclasses
    OUTCLASS = specs
    # After transferring output at /cfunas/exp remove a copy available at permanent storage of HPC
    # [Default: Do set "TRUE"]. BOOLEAN = TRUE, FALSE
    MODEL_output_remove = TRUE
    # Activate cmorization [Default: leave empty]. BOOLEAN = TRUE, FALSE
    CMORIZATION = TRUE
    # Essential if cmorization is activated.
    # STRING =  (http://www.specs-fp7.eu/wiki/images/1/1c/SPECS_standard_output.pdf)
    CMORFAMILY =
    # Supply the name of the experiment associated (if there is any) otherwise leave it empty.
    # STRING (with space) = seasonal r1p1, seaiceinit r?p?
    ASSOCIATED_EXPERIMENT =
    # Essential if cmorization is activated (Forcing). STRING = Nat,Ant (Nat and Ant is a single option)
    FORCING =
    # Essential if cmorization is activated (Initialization description). STRING = N/A
    INIT_DESCR =
    # Essential if cmorization is activated (Physics description). STRING = N/A
    PHYS_DESCR =
    # Essential if cmorization is activated (Associated model). STRING = N/A
    ASSOC_MODEL =

    [grid]
    # AGCM grid resolution, horizontal (truncation T) and vertical (levels L).
    # STRING = T159L62, T255L62, T255L91, T511L91, T799L62 (IFS)
    IFS_resolution = T511L91
    # OGCM grid resolution. STRING = ORCA1L46, ORCA1L75, ORCA025L46, ORCA025L75 (NEMO)
    NEMO_resolution = ORCA025L75

    [oasis]
    # Coupler (OASIS) options.
    OASIS3 = yes
    # Number of pseduo-parallel cores for coupler [Default: Do set "7"]. NUMERIC = 1, 7, 10
    OASIS_nproc = 7
    # Handling the creation of coupling fields dynamically [Default: Do set "TRUE"].
    # BOOLEAN = TRUE, FALSE
    OASIS_flds = TRUE

    [ifs]
    # Atmospheric initial conditions ready to be used.
    # STRING = ID found here : https://earth.bsc.es/wiki/doku.php?id=initial_conditions:atmospheric
    ATM_ini =
    # A different IC member per EXPID member ["PERT"] or which common IC member
    # for all EXPID members ["fc0" / "fc1"]. String = PERT/fc0/fc1...
    ATM_ini_member =
    # Set timestep (in sec) w.r.t resolution.
    # NUMERIC = 3600 (T159), 2700 (T255), 900 (T511), 720 (T799)
    IFS_timestep = 900
    # Number of parallel cores for AGCM component. NUMERIC = 28, 100
    IFS_nproc = 640
    # Coupling frequency (in hours) [Default: Do set "3"]. NUMERIC = 3, 6
    RUN_coupFreq = 3
    # Post-procssing frequency (in hours) [Default: Do set "6"]. NUMERIC = 3, 6
    NFRP = 6
    # [Default: Do set "TRUE"]. BOOLEAN = TRUE, FALSE
    LCMIP5 = TRUE
    # Choose RCP value [Default: Do set "2"]. NUMERIC = 0, 1=3-PD, 2=4.5, 3=6, 4=8.5
    NRCP = 0
    # [Default: Do set "TRUE"]. BOOLEAN = TRUE, FALSE
    LHVOLCA = TRUE
    # [Default: Do set "0"]. NUMERIC = 1850, 2005
    NFIXYR = 0
    # Save daily output or not [Default: Do set "FALSE"]. BOOLEAN = TRUE, FALSE
    SAVEDDA = FALSE
    # Save reduced daily output or not [Default: Do set "FALSE"]. BOOLEAN = TRUE, FALSE
    ATM_REDUCED_OUTPUT = FALSE
    # Store grib codes from SH files [User need to refer defined  ppt* files for the experiment]
    ATM_SH_CODES =
    # Store levels against "ATM_SH_CODES" e.g: level1,level2,level3, ...
    ATM_SH_LEVELS =
    # Store grib codes from GG files [User need to refer defined  ppt* files for the experiment]
    ATM_GG_CODES =
    # Store levels against "ATM_GG_CODES" (133.128, 246.128, 247.128, 248.128)
    # e.g: level1,level2,level3, ...
    ATM_GG_LEVELS =
    # SPPT stochastic physics active or not [Default: set "FALSE"]. BOOLEAN = TRUE, FALSE
    LSPPT = FALSE
    # Write the perturbation patterns for SPPT or not [Default: set "FALSE"].
    # BOOLEAN = TRUE, FALSE
    LWRITE_ARP =
    # Number of scales for SPPT [Default: set 3]. NUMERIC = 1, 2, 3
    NS_SPPT =
    # Standard deviations of each scale [Default: set 0.50,0.25,0.125]
    # NUMERIC values separated by ,
    SDEV_SPPT =
    # Decorrelation times (in seconds) for each scale [Default: set 2.16E4,2.592E5,2.592E6]
    # NUMERIC values separated by ,
    TAU_SPPT =
    # Decorrelation lengths (in meters) for each scale [Default: set 500.E3,1000.E3,2000.E3]
    # NUMERIC values separated by ,
    XLCOR_SPPT =
    # Clipping ratio (number of standard deviations) for SPPT [Default: set 2] NUMERIC
    XCLIP_SPPT =
    # Stratospheric tapering in SPPT [Default: set "TRUE"]. BOOLEAN = TRUE, FALSE
    LTAPER_SPPT =
    # Top of stratospheric tapering layer in Pa [Default: set to 50.E2] NUMERIC
    PTAPER_TOP =
    # Bottom of stratospheric tapering layer in Pa [Default: set to 100.E2] NUMERIC
    PTAPER_BOT =
    ## ATMOSPHERIC NUDGING PARAMETERS ##
    # Atmospheric nudging towards reinterpolated ERA-Interim data. BOOLEAN = TRUE, FALSE
    ATM_NUDGING = FALSE
    # Atmospheric nudging reference data experiment name. [T255L91: b0ir]
    ATM_refnud =
    # Nudge vorticity. BOOLEAN = TRUE, FALSE
    NUD_VO =
    # Nudge divergence. BOOLEAN = TRUE, FALSE
    NUD_DI =
    # Nudge temperature. BOOLEAN = TRUE, FALSE
    NUD_TE =
    # Nudge specific humidity. BOOLEAN = TRUE, FALSE
    NUD_Q =
    # Nudge liquid water content. BOOLEAN = TRUE, FALSE
    NUD_QL =
    # Nudge ice water content. BOOLEAN = TRUE, FALSE
    NUD_QI =
    # Nudge cloud fraction. BOOLEAN = TRUE, FALSE
    NUD_QC =
    # Nudge log of surface pressure. BOOLEAN = TRUE, FALSE
    NUD_LP =
    # Relaxation coefficient for vorticity. NUMERIC in ]0,inf[;
    # 1 means half way between model value and ref value
    ALPH_VO =
    # Relaxation coefficient for divergence. NUMERIC in ]0,inf[;
    # 1 means half way between model value and ref value
    ALPH_DI =
    # Relaxation coefficient for temperature. NUMERIC in ]0,inf[;
    # 1 means half way between model value and ref value
    ALPH_TE =
    # Relaxation coefficient for specific humidity. NUMERIC in ]0,inf[;
    # 1 means half way between model value and ref value
    ALPH_Q =
    # Relaxation coefficient for log surface pressure. NUMERIC in ]0,inf[;
    # 1 means half way between model value and ref value
    ALPH_LP =
    # Nudging area Northern limit [Default: Do set "90"]
    NUD_NLAT =
    # Nudging area Southern limit [Default: Do set "-90"]
    NUD_SLAT =
    # Nudging area Western limit NUMERIC in [0,360] [Default: Do set "0"]
    NUD_WLON =
    # Nudging area Eastern limit NUMERIC in [0,360] [Default: Do set "360"; E<W will span Greenwich]
    NUD_ELON =
    # Nudging vertical levels : lower level [Default: Do set "1"]
    NUD_VMIN =
    # Nudging vertical levels : upper level [Default: Do set to number of vertical levels]
    NUD_VMAX =

    [nemo]
    # Ocean initial conditions ready to be used. [Default: leave empty].
    # STRING = ID found here : https://earth.bsc.es/wiki/doku.php?id=initial_conditions:oceanic
    OCEAN_ini =
    # A different IC member per EXPID member ["PERT"] or which common IC member
    # for all EXPID members ["fc0" / "fc1"]. String = PERT/fc0/fc1...
    OCEAN_ini_member =
    # Set timestep (in sec) w.r.t resolution. NUMERIC = 3600 (ORCA1), 1200 (ORCA025)
    NEMO_timestep = 1200
    # Number of parallel cores for OGCM component. NUMERIC = 16, 24, 36
    NEMO_nproc = 960
    # Ocean Advection Scheme [Default: Do set "tvd"]. STRING = tvd, cen2
    ADVSCH = cen2
    # Nudging activation. BOOLEAN = TRUE, FALSE
    OCEAN_NUDGING = FALSE
    # Toward which data to nudge; essential if "OCEAN_NUDGING" is TRUE.
    # STRING = fa9p, s4, glorys2v1
    OCEAN_NUDDATA = FALSE
    # Rebuild and store restarts to HSM for an immediate prediction experiment.
    # BOOLEAN = TRUE, FALSE
    OCEAN_STORERST = FALSE

    [ice]
    # Sea-Ice Model [Default: Do set "LIM2"]. STRING = LIM2, LIM3
    ICE = LIM3
    # Sea-ice initial conditions ready to be used. [Default: leave empty].
    # STRING = ID found here : https://earth.bsc.es/wiki/doku.php?id=initial_conditions:sea_ice
    ICE_ini =
    # A different IC member per EXPID member ["PERT"] or which common IC member
    # for all EXPID members ["fc0" / "fc1"]. String = PERT/fc0/fc1...
    ICE_ini_member =
    # Set timestep (in sec) w.r.t resolution. NUMERIC = 3600 (ORCA1), 1200 (ORCA025)
    LIM_timestep = 1200

    [pisces]
    # Activate PISCES (TRUE) or not (FALSE) [Default: leave empty]
    PISCES = FALSE
    # PISCES initial conditions ready to be used. [Default: leave empty].
    # STRING = ID found here : https://earth.bsc.es/wiki/doku.php?id=initial_conditions:biogeochemistry
    PISCES_ini =
    # Set timestep (in sec) w.r.t resolution. NUMERIC = 3600 (ORCA1), 3600 (ORCA025)
    PISCES_timestep = 3600


Finally, you can launch Autosubmit *run* in background and with ``nohup`` (continue running although the user who launched the process logs out).
::

    nohup autosubmit run cxxx &

Fourth Step: Experiment monitor
-------------------------------

The following procedure could be adopted to generate the plots for visualizing the status of the experiment at any instance.
With this command we can generate new plots to check which is the status of the experiment. Different job status are represented with different colors.

::

    autosubmit monitor  cxxx

The location where user can find the generated plots with date and timestamp can be found below:

::

    <experiments_directory>/cxxx/plot/cxxx_<date>_<time>.pdf

