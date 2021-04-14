.. _grouping:

Grouping jobs
=============================

Other than the filters, another option for large workflows is to group jobs. This option is available with the ``group_by`` keyword, which can receive the values ``{date,member,chunk,split,automatic}``.

For the first 4 options, the grouping criteria is explicitly defined ``{date,member,chunk,split}``.
In addition to that, it is possible to expand some dates/members/chunks that would be grouped either/both by status or/and by specifying the date/member/chunk not to group.
The syntax used in this option is almost the same as for the filters, in the format of ``[ date1 [ member1 [ chunk1 chunk2 ] member2 [ chunk3 ... ] ... ] date2 [ member3 [ chunk1 ] ] ... ]``

.. important:: The grouping option is also in autosubmit monitor, create, setstatus and recovery

Examples:

Consider the following workflow:

.. figure:: ../workflows/pre_grouping_workflow.png
   :name: pre_grouping_workflow
   :align: center
   :alt: simple workflow

**Group by date**

::

    -group_by=date

.. figure:: ../workflows/group_date.png
   :name: group_date
   :width: 70%
   :align: center
   :alt: group date

::

    -group_by=date -expand="[ 20000101 ]"

.. figure:: ../workflows/group_by_date_expand.png
   :name: group_date_expand
   :width: 70%
   :align: center
   :alt: group date expand


::

    -group_by=date -expand_status="FAILED RUNNING"

.. figure:: ../workflows/group_by_date_status.png
   :name: group_date_status_expand
   :width: 70%
   :align: center
   :alt: group date expand status

::

    -group_by=date -expand="[ 20000101 ]" -expand_status="FAILED RUNNING"

.. figure:: ../workflows/group_by_date_status_expand.png
   :name: group_date_expand_status
   :width: 100%
   :align: center
   :alt: group date expand status

**Group by member**

::

    -group_by=member

.. figure:: ../workflows/group_member.png
   :name: group_member
   :width: 70%
   :align: center
   :alt: group member


::

    -group_by=member -expand="[ 20000101 [ fc0 fc1 ] 20000202 [ fc0 ] ]"

.. figure:: ../workflows/group_by_member_expand.png
   :name: group_member_expand
   :width: 70%
   :align: center
   :alt: group member expand

::

    -group_by=member -expand_status="FAILED QUEUING"

.. figure:: ../workflows/group_by_member_status.png
   :name: group_member_status
   :width: 70%
   :align: center
   :alt: group member expand

::

    -group_by=member -expand="[ 20000101 [ fc0 fc1 ] 20000202 [ fc0 ] ]" -expand_status="FAILED QUEUING"

.. figure:: ../workflows/group_by_member_expand_status.png
   :name: group_member_expand_status
   :width: 70%
   :align: center
   :alt: group member expand

**Group by chunk**

::

    -group_by=chunk

.. figure:: ../workflows/group_chunk.png
   :name: group_chunk
   :width: 70%
   :align: center
   :alt: group chunk

Sychronize jobs

If there are jobs synchronized between members or dates, then a connection between groups is shown:

.. figure:: ../workflows/group_synchronize.png
   :name: group_synchronize
   :width: 70%
   :align: center
   :alt: group synchronize

::

    -group_by=chunk -expand="[ 20000101 [ fc0 [1 2] ] 20000202 [ fc1 [2] ] ]"

.. figure:: ../workflows/group_by_chunk_expand.png
   :name: group_chunk_expand
   :width: 70%
   :align: center
   :alt: group chunk expand

::

    -group_by=chunk -expand_status="FAILED RUNNING"

.. figure:: ../workflows/group_by_chunk_status.png
   :name: group_chunk_status
   :width: 70%
   :align: center
   :alt: group chunk expand

::

    -group_by=chunk -expand="[ 20000101 [ fc0 [1] ] 20000202 [ fc1 [1 2] ] ]" -expand_status="FAILED RUNNING"

.. figure:: ../workflows/group_by_chunk_expand_status.png
   :name: group_chunk_expand_status
   :width: 70%
   :align: center
   :alt: group chunk expand

**Group by split**

If there are chunk jobs that are split, the splits can also be grouped.

.. figure:: ../workflows/split_workflow.png
   :name: split_workflow
   :width: 70%
   :align: center
   :alt: split workflow

::

    -group_by=split

.. figure:: ../workflows/split_group.png
   :name: group_split
   :width: 70%
   :align: center
   :alt: group split

**Understading the group status**

If there are jobs with different status grouped together, the status of the group is determined as follows:
If there is at least one job that failed, the status of the group will be FAILED. If there are no failures, but if there is at least one job running, the status will be RUNNING.
The same idea applies following the hierarchy: SUBMITTED, QUEUING, READY, WAITING, SUSPENDED, UNKNOWN. If the group status is COMPLETED, it means that all jobs in the group were completed.

**Automatic grouping**

For the automatic grouping, the groups are created by collapsing the split->chunk->member->date that share the same status (following this hierarchy).
The following workflow automatic created the groups 20000101_fc0, since all the jobs for this date and member were completed, 20000101_fc1_3, 20000202_fc0_2, 20000202_fc0_3 and 20000202_fc1, as all the jobs up to the respective group granularities share the same - waiting - status.

For example:

.. figure:: ../workflows/group_automatic.png
   :name: group_automatic
   :width: 70%
   :align: center
   :alt: group automatic

Especially in the case of monitoring an experiment with a very large number of chunks, it might be useful to hide the groups created automatically. This allows to better visualize the chunks in which there are jobs with different status, which can be a good indication that there is something currently happening within such chunks (jobs ready, submitted, running, queueing or failed).

::

    -group_by=automatic --hide_groups
