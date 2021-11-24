How to check the experiment configuration
=========================================
To check the configuration of the experiment, use the command:
::

    autosubmit check EXPID

*EXPID* is the experiment identifier.

It checks experiment configuration and warns about any detected error or inconsistency.
It is used to check if the script is well-formed.
If any template has an inconsistency it will replace them for an empty value on the cmd generated.
Options:
::

    usage: autosubmit check [-h -nt] expid

      expid                 experiment identifier
      -nt                   --notransitive
                                prevents doing the transitive reduction when plotting the workflow
      -h, --help            show this help message and exit

Example:
::

    autosubmit check cxxx

How to use check in running time:
========================

In ``jobs_cxxx.conf`` , you can set check(default true) to check the scripts during autosubmit run cxx.

There are two parameters related to check:

* CHECK: Controls the mechanism that allows replacing an unused variable with an empty string ( %_% substitution). It is TRUE by default.

* SHOW_CHECK_WARNINGS: For debugging purposes. It will print a lot of information regarding variables and substitution if it is set to TRUE.

.. code-block:: ini

    CHECK = TRUE or FALSE or ON_SUBMISSION # Default is TRUE
    SHOW_CHECK_WARNINGS = TRUE or FALSE # Default is FALSE



::

    CHECK = TRUE # Static templates (existing on `autosubmit create`). Used to substitute empty variables

    CHECK = ON_SUBMISSION # Dynamic templates (generated on running time). Used to substitute empty variables.

    CHECK = FALSE # Used to disable this substitution.

::

    SHOW_CHECK_WARNINGS = TRUE # Shows a LOT of information. Disabled by default.


For example:

.. code-block:: ini

    [LOCAL_SETUP]
    FILE = filepath_that_exists
    PLATFORM = LOCAL
    WALLCLOCK = 05:00
    CHECK = TRUE
    SHOW_CHECK_WARNINGS = TRUE
    ...
    [SIM]
    FILE = filepath_that_no_exists_until_setup_is_processed
    PLATFORM = bsc_es
    DEPENDENCIES = LOCAL_SETUP SIM - 1
    RUNNING = chunk
    WALLCLOCK = 05:00
    CHECK = on_submission
    SHOW_CHECK_WARNINGS = FALSE
    ...


