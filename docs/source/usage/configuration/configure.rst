How to configure email notifications
====================================

To configure the email notifications, you have to follow two configuration steps:

1. First you have to enable email notifications and set the accounts where you will receive it.

Edit ``autosubmit_cxxx.conf`` in the ``conf`` folder of the experiment.

.. hint::
    Remember that you can define more than one email address divided by a whitespace.

Example:
::

    vi <experiments_directory>/cxxx/conf/autosubmit_cxxx.conf

.. code-block:: ini

    [mail]
    # Enable mail notifications
    # Default = False
    NOTIFICATIONS = True
    # Mail address where notifications will be received
    TO =  jsmith@example.com  rlewis@example.com

2. Then you have to define for which jobs you want to be notified.

Edit ``jobs_cxxx.conf`` in the ``conf`` folder of the experiment.

.. hint::
    You will be notified every time the job changes its status to one of the statuses
    defined on the parameter ``NOTIFY_ON``

.. hint::
    Remember that you can define more than one job status divided by a whitespace.

Example:
::

    vi <experiments_directory>/cxxx/conf/jobs_cxxx.conf

.. code-block:: ini

    [LOCAL_SETUP]
    FILE = LOCAL_SETUP.sh
    PLATFORM = LOCAL
    NOTIFY_ON = FAILED COMPLETED


How to request exclusivity or reservation
=========================================

To request exclusivity or reservation for your jobs, you can configure two platform variables:

Edit ``platforms_cxxx.conf`` in the ``conf`` folder of the experiment.

.. hint::
    Until now, it is only available for Marenostrum.

.. hint::
    To define some jobs with exclusivity/reservation and some others without it, you can define
    twice a platform, one with this parameters and another one without it.

Example:
::

    vi <experiments_directory>/cxxx/conf/platforms_cxxx.conf

.. code-block:: ini

    [marenostrum3]
    TYPE = LSF
    HOST = mn-bsc32
    PROJECT = bsc32
    ADD_PROJECT_TO_HOST = false
    USER = bsc32XXX
    SCRATCH_DIR = /gpfs/scratch
    TEST_SUITE = True
    EXCLUSIVITY = True

Of course, you can configure only one or both. For example, for reservation it would be:

Example:
::

    vi <experiments_directory>/cxxx/conf/platforms_cxxx.conf

.. code-block:: ini

    [marenostrum3]
    TYPE = LSF
    ...
    RESERVATION = your-reservation-id