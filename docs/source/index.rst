:html_theme.sidebar_secondary.remove:

.. autosubmit documentation master file, created by
   sphinx-quickstart on Wed Mar 18 16:55:44 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

############################
Autosubmit Workflow Manager
############################

.. toctree::
   :maxdepth: 1
   :hidden:

   /introduction/index

.. toctree::
   :caption: Quick Start Guide
   :maxdepth: 1
   :hidden:

   /qstartguide/index

.. toctree::
   :caption: Installation
   :maxdepth: 1
   :hidden:

   /installation/index

.. toctree::
   :caption: User Guide
   :maxdepth: 2
   :hidden:

   /userguide/index
   /userguide/create/index
   /userguide/configure/index
   /userguide/defining_workflows/index
   /userguide/wrappers/index
   /userguide/run/index
   /userguide/modifying_workflow/index
   /userguide/manage/index
   /userguide/monitor_and_check/index
   /userguide/set_and_share_the_configuration/index
   /userguide/variables
   /userguide/expids
   /userguide/provenance

.. toctree::
   :caption: Database Documentation
   :maxdepth: 1
   :hidden:

   /database/index

.. toctree::
   :caption: Developer Guide
   :maxdepth: 1
   :hidden:

   /devguide/index

.. toctree::
   :caption: Troubleshooting
   :maxdepth: 1
   :hidden:

   /troubleshooting/index
   /troubleshooting/error-codes
   /troubleshooting/changelog

.. toctree::
   :caption: Module Documentation
   :maxdepth: 1
   :hidden:

   /moduledoc/index


.. raw:: html

   <div>
        <div class="row gap-4">
            <div class="col d-flex flex-column justify-content-center">
                <h1 class="fw-bold">Autosubmit workflow manager</h1>
                <p>Autosubmit is a Python software to manage complicated workflows on HPC platforms</p>
                <div class="m-2 bg-black text-white font-monospace">autosubmit expid -H HPCname -d Description</div>
                <div class="mt-3 mx-2 d-flex gap-2">
                  <a class="btn text-white rounded-pill px-3" style="background-color: #4E8490;" href="qstartguide/index.html">Get started</a>
                  <a class="btn text-white rounded-pill px-3" style="background-color: #4E8490;" href="installation/index.html">Installation</a>
                </div>
            </div>
            <div class="col my-2" style="min-width: 20rem;">
                <img src="_static/isometric.svg" style="background-color: transparent;"/>
                <label class="w-100 text-end mt-2" style="opacity: 0.25; font-size: 0.7rem;">Illustration by Storyset</label>
            </div>
        </div>

        <div class="row gap-4">
            <div class="col" style="min-width: 20rem;">
                <i class="fa-solid fa-gear fs-2" style="color: #4E8490;"></i>
                <div class="fs-4">Automatization</div>
                <p>Autosubmit manages job submission and dependencies without user intervention</p>
            </div>
            <div class="col" style="min-width: 20rem;">
                <i class="fa-solid fa-fingerprint fs-2" style="color: #4E8490;"></i>
                <div class="fs-4">Data Provenance</div>
                <p>Autosubmit assigns unique ID's to experiments, uses open standards, and applies other techniques to enable data provenance in the experiments and workflows</p>
            </div>
            <div class="col" style="min-width: 20rem;">
                <i class="fa-solid fa-clock-rotate-left fs-2" style="color: #4E8490;"></i>
                <div class="fs-4">Failure Tolerance</div>
                <p>Autosubmit manages automatic retrials and has the ability to rerun specific parts of the experiment in case of failure</p>
            </div>
            <div class="col" style="min-width: 20rem;">
                <i class="fa-solid fa-sitemap fs-2" style="color: #4E8490;"></i>
                <div class="fs-4">Resource Management</div>
                <p>Autosubmit supports a per-platform configuration, allowing users to run their experiments without adapting job scripts</p>
            </div>
            <div class="col" style="min-width: 20rem;">
                <i class="fa-solid fa-server fs-2" style="color: #4E8490;"></i>
                <div class="fs-4">Multiple Platform</div>
                <p>Autosubmit can run jobs of an experiment in different platforms</p>
            </div>
        </div>
    </div>