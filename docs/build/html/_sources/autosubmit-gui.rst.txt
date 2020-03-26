Autosubmit GUI
##############

.. _autosubmitGUIMP:

Autosubmit GUI Main Page
========================

Inside the Barcelona Supercomputing Network, you can go to: http://bscesweb04.bsc.es/autosubmitapp/ to get access to a graphic user interface that allows you to easily monitor your experiments and those of your colleagues. This Web App introduces many useful features for experiment monitoring, and we are continuously improving it.


When you enter the site, you will be presented with the following page: 

.. figure:: /agui/fig1_gui.png
   :name: first_page
   :width: 100%
   :align: center
   :alt: autosubmit guide

   Welcome page

From here you can insert text in the Search input box and press **Search**, the search engine will look for coincidences of your input string to the descripcion, owner, or name of the experiment. The results will be shown below ordered by status, experiments ``RUNNING`` will be shown in the first rows. You can also click on the ``Running`` button, and all the experiments that are currently running will be listed. The results will look like:

.. figure:: /agui/fig2_gui.png
   :name: first_page_search
   :width: 100%
   :align: center
   :alt: result search

   Search Result

If you click on ``Show Detailed Data``, summary data for each experiment (result) will be loaded. This will add some data to each experiment as well as change some colors depending on conditions that are explained below.

.. figure:: /agui/fig3_gui.png
   :name: first_page_search_plus
   :width: 100%
   :align: center
   :alt: result search plus

   Search Result plus Detailed Data

For each experiment, you see the following data:

- *Experiment Name*
- *Progress Bar*: Shows completed jobs / total jobs. It turns red when there are **failed** jobs in the experiment, but **Show Detailed Data** should have been requested.
- *Experiment Status*: *RUNNING* or *NOT RUNNING*.
- *Owner*
- *Experiment Description*
- *Refresh button*: It will say *Summary* when the detailed data has not been requested. If it says *Summary* and you click on it, it will load datailed data for that experiment, otherwise it will refresh the existing detailed data.
- *More button*: Opens the **Experiment Page**.
- *Average Queue Time* for all jobs.
- *Average Run Time* for all jobs.
- *Number of Running Jobs*
- *Number of Queuing Jobs*
- *Number of Submitted Jobs*
- *Number of Suspended Jobs*
- *Number of Failed Jobs*: If there are Failed jobs, a list of the names of those jobs will be displayed.

After clicking on the **MORE** button, you will be presented with the **Experiment Page**, which is the main view that Autosubmit provides. These are its main components:

.. toctree::
   agui/experiment
   agui/tree
   agui/graph
   agui/log
   agui/statistics