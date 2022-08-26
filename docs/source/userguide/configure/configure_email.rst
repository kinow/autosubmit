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
    # Enable mail notifications for remote_failures
    # Default = True
    NOTIFY_ON_REMOTE_FAIL = True
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
