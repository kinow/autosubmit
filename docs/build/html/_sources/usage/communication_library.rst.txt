How to change the communications library
=====================================

In order to handle the remote communications with the different platforms, Autosubmit uses an implementation
of a communications library. There are multiple implementations, so you can choose any of them.

.. hint::
    At this moment there are one available communication library which is ``paramiko``.

To change the communications library, open the <experiments_directory>/cxxx/conf/autosubmit_cxxx.conf file
where cxxx is the experiment identifier and change the value of the API configuration variable in the communications
section:

.. code-block:: ini

    [communications]
    # Communications library used to connect with platforms: paramiko.
    # Default = paramiko
    API = paramiko