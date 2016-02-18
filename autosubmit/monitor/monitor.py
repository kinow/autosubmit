#!/usr/bin/env python

# Copyright 2015 Earth Sciences Department, BSC-CNS

# This file is part of Autosubmit.

# Autosubmit is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Autosubmit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Autosubmit.  If not, see <http://www.gnu.org/licenses/>.
import datetime
import os

import time
from os import path
from os import chdir
from os import listdir
from os import remove

import pydotplus


# These packages produce errors when added to setup.
# noinspection PyPackageRequirements
import numpy as np
# noinspection PyPackageRequirements
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches

import subprocess

from autosubmit.job.job_common import Status
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.config.log import Log


class Monitor:
    """Class to handle monitoring of Jobs at HPC."""
    _table = dict([(Status.UNKNOWN, 'white'), (Status.WAITING, 'gray'), (Status.READY, 'lightblue'),
                   (Status.SUBMITTED, 'cyan'), (Status.QUEUING, 'lightpink'), (Status.RUNNING, 'green'),
                   (Status.COMPLETED, 'yellow'), (Status.FAILED, 'red'), (Status.SUSPENDED, 'orange')])

    @staticmethod
    def color_status(status):
        """
        Return color associated to given status

        :param status: status
        :type status: Status
        :return: color
        :rtype: str
        """
        if status == Status.WAITING:
            return Monitor._table[Status.WAITING]
        elif status == Status.READY:
            return Monitor._table[Status.READY]
        elif status == Status.SUBMITTED:
            return Monitor._table[Status.SUBMITTED]
        elif status == Status.QUEUING:
            return Monitor._table[Status.QUEUING]
        elif status == Status.RUNNING:
            return Monitor._table[Status.RUNNING]
        elif status == Status.COMPLETED:
            return Monitor._table[Status.COMPLETED]
        elif status == Status.FAILED:
            return Monitor._table[Status.FAILED]
        elif status == Status.SUSPENDED:
            return Monitor._table[Status.SUSPENDED]
        else:
            return Monitor._table[Status.UNKNOWN]

    def create_tree_list(self, expid, joblist):
        """
        Create graph from joblist

        :param expid: experiment's identifier
        :type expid: str
        :param joblist: joblist to plot
        :type joblist: JobList
        :return: created graph
        :rtype: pydotplus.Dot
        """
        Log.debug('Creating workflow graph...')
        graph = pydotplus.Dot(graph_type='digraph')

        Log.debug('Creating legend...')
        legend = pydotplus.Subgraph(graph_name='Legend', label='Legend', rank="source")
        legend.add_node(pydotplus.Node(name='WAITING', shape='box', style="filled",
                                       fillcolor=self._table[Status.WAITING]))
        legend.add_node(pydotplus.Node(name='READY', shape='box', style="filled",
                                       fillcolor=self._table[Status.READY]))
        legend.add_node(
            pydotplus.Node(name='SUBMITTED', shape='box', style="filled", fillcolor=self._table[Status.SUBMITTED]))
        legend.add_node(pydotplus.Node(name='QUEUING', shape='box', style="filled",
                                       fillcolor=self._table[Status.QUEUING]))
        legend.add_node(pydotplus.Node(name='RUNNING', shape='box', style="filled",
                                       fillcolor=self._table[Status.RUNNING]))
        legend.add_node(
            pydotplus.Node(name='COMPLETED', shape='box', style="filled", fillcolor=self._table[Status.COMPLETED]))
        legend.add_node(pydotplus.Node(name='FAILED', shape='box', style="filled",
                                       fillcolor=self._table[Status.FAILED]))
        legend.add_node(
            pydotplus.Node(name='SUSPENDED', shape='box', style="filled", fillcolor=self._table[Status.SUSPENDED]))
        graph.add_subgraph(legend)

        exp = pydotplus.Subgraph(graph_name='Experiment', label=expid)
        self.nodes_ploted = set()
        Log.debug('Creating job graph...')
        for job in joblist:
            if job.has_parents():
                continue

            node_job = pydotplus.Node(job.name, shape='box', style="filled",
                                      fillcolor=self.color_status(job.status))
            exp.add_node(node_job)
            self._add_children(job, exp, node_job)

        graph.add_subgraph(exp)
        Log.debug('Graph definition finalized')
        return graph

    def _add_children(self, job, exp, node_job):
        if job in self.nodes_ploted:
            return
        self.nodes_ploted.add(job)
        if job.has_children() != 0:
            for child in sorted(job.children, key=lambda k: k.name):
                node_child = exp.get_node(child.name)
                if len(node_child) == 0:
                    node_child = pydotplus.Node(child.name, shape='box', style="filled",
                                                fillcolor=self.color_status(child.status))
                    exp.add_node(node_child)
                    flag = True
                else:
                    node_child = node_child[0]
                    flag = False
                exp.add_edge(pydotplus.Edge(node_job, node_child))
                if flag:
                    self._add_children(child, exp, node_child)

    def generate_output(self, expid, joblist, output_format="pdf", show=False):
        """
        Plots graph for joblist and stores it in a file

        :param expid: experiment's identifier
        :type expid: str
        :param joblist: joblist to plot
        :type joblist: JobList
        :param output_format: file format for plot
        :type output_format: str (png, pdf, ps)
        :param show: if true, will open the new plot with the default viewer
        :type show: bool
        """
        Log.info('Plotting...')
        now = time.localtime()
        output_date = time.strftime("%Y%m%d_%H%M", now)
        output_file = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "plot", expid + "_" + output_date + "." +
                                   output_format)

        graph = self.create_tree_list(expid, joblist)

        Log.debug("Saving workflow plot at '{0}'", output_file)
        if output_format == "png":
            # noinspection PyUnresolvedReferences
            graph.write_png(output_file)
        elif output_format == "pdf":
            # noinspection PyUnresolvedReferences
            graph.write_pdf(output_file)
        elif output_format == "ps":
            # noinspection PyUnresolvedReferences
            graph.write_ps(output_file)
        elif output_format == "svg":
            # noinspection PyUnresolvedReferences
            graph.write_svg(output_file)
        else:
            Log.error('Format {0} not supported', output_format)
            return
        Log.result('Plot created at {0}', output_file)
        if show:
            try:
                subprocess.check_call(['xdg-open', output_file])
            except subprocess.CalledProcessError:
                Log.error('File {0} could not be opened', output_file)

    def generate_output_stats(self, expid, joblist, output_format="pdf", period_ini=None, period_fi=None, show=False):
        """
        Plots stats for joblist and stores it in a file

        :param expid: experiment's identifier
        :type expid: str
        :param joblist: joblist to plot
        :type joblist: JobList
        :param output_format: file format for plot
        :type output_format: str (png, pdf, ps)
        :param period_ini: initial datetime of filtered period
        :type period_ini: datetime
        :param period_fi: final datetime of filtered period
        :type period_fi: datetime
        :param show: if true, will open the new plot with the default viewer
        :type show: bool
        """
        Log.info('Creating stats file')
        now = time.localtime()
        output_date = time.strftime("%Y%m%d_%H%M", now)
        output_file = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "plot", expid + "_statistics_" + output_date +
                                   "." + output_format)
        self.create_bar_diagram(expid, joblist, output_file, period_ini, period_fi)
        Log.result('Stats created at {0}', output_file)
        if show:
            try:
                subprocess.check_call(['xdg-open', output_file])
            except subprocess.CalledProcessError:
                Log.error('File {0} could not be opened', output_file)

    @staticmethod
    def create_bar_diagram(expid, joblist, output_file, period_ini=None, period_fi=None):
        """
        Function to plot statistics

        :param expid: experiment's identifier
        :type expid: str
        :param joblist: joblist to plot
        :type joblist: JobList
        :param output_file: path to create file
        :type output_file: str
        :param period_ini: initial datetime of filtered period
        :type period_ini: datetime
        :param period_fi: final datetime of filtered period
        :type period_fi: datetime
        """

        def timedelta2hours(deltatime):
            return deltatime.days * 24 + deltatime.seconds / 3600.0

        total_jobs_submitted = 0
        cpu_consumption = datetime.timedelta()
        real_consumption = datetime.timedelta()
        total_jobs_run = 0
        total_jobs_failed = 0
        total_jobs_completed = 0
        expected_cpu_consumption = 0
        expected_real_consumption = 0
        threshold = 0
        for job in joblist:
            total_jobs_submitted += len(job.check_retrials_submit_time())
            if job.wallclock:
                l = job.wallclock.split(':')
                hours = float(l[1]) / 60 + float(l[0])
            else:
                hours = 0
            threshold = max(threshold, hours)
            expected_cpu_consumption += hours * int(job.processors)
            expected_real_consumption += hours
        # These are constants, so they need to be CAPS. Suppress PyCharm warning
        # noinspection PyPep8Naming
        MAX = 12.0
        # noinspection PyPep8Naming
        N = len(joblist)
        num_plots = int(np.ceil(N / MAX))

        ind = np.arange(int(MAX))  # the x locations for the groups
        width = 0.16  # the width of the bars

        plt.close('all')

        # noinspection PyPep8Naming
        RATIO = 4
        fig = plt.figure(figsize=(RATIO * 4, 3 * RATIO * num_plots))
        gs = gridspec.GridSpec(RATIO * num_plots + 2, 1)
        fig.suptitle('STATS - ' + expid, fontsize=24, fontweight='bold')

        ax = []
        ax2 = []
        max_time = 0
        max_fail = 0
        for plot in range(1, num_plots + 1):
            ax.append(fig.add_subplot(gs[RATIO * plot - RATIO + 2:RATIO * plot + 1]))
            ax2.append(ax[plot - 1].twinx())
            l1 = int((plot - 1) * MAX)
            l2 = int(plot * MAX)

            run = [datetime.timedelta()] * (l2 - l1)
            queued = [datetime.timedelta()] * (l2 - l1)
            failed_jobs = [0] * (l2 - l1)
            fail_queued = [datetime.timedelta()] * (l2 - l1)
            fail_run = [datetime.timedelta()] * (l2 - l1)

            for i, job in enumerate(joblist[l1:l2]):
                submit_times = job.check_retrials_submit_time()
                start_times = job.check_retrials_start_time()
                end_times = job.check_retrials_end_time()

                for j, t in enumerate(submit_times):

                    if j >= len(end_times):
                        if j < len(start_times):
                            queued[i] += start_times[j] - submit_times[j]
                    elif j == (len(submit_times) - 1) and job.status == Status.COMPLETED:
                        queued[i] += start_times[j] - submit_times[j]
                        run[i] += end_times[j] - start_times[j]
                        cpu_consumption += run[i] * int(job.processors)
                        real_consumption += run[i]
                    else:
                        failed_jobs[i] += 1
                        fail_queued[i] += start_times[j] - submit_times[j]
                        fail_run[i] += end_times[j] - start_times[j]
                        cpu_consumption += fail_run[i] * int(job.processors)
                        real_consumption += fail_run[i]
                total_jobs_run += len(start_times)
                total_jobs_failed += failed_jobs[i]
                total_jobs_completed += len(end_times) - failed_jobs[i]
            max_timedelta = max(max(max(run, fail_run, queued, fail_queued)), datetime.timedelta(hours=threshold))
            max_time = max(max_time, max_timedelta.days * 24 + max_timedelta.seconds / 3600.0)
            max_fail = max(max_fail, max(failed_jobs))

            for i, delta in enumerate(queued):
                queued[i] = timedelta2hours(delta)

            for i, delta in enumerate(run):
                run[i] = timedelta2hours(delta)

            for i, delta in enumerate(fail_queued):
                fail_queued[i] = timedelta2hours(delta)

            for i, delta in enumerate(fail_run):
                fail_run[i] = timedelta2hours(delta)

            rects1 = ax[plot - 1].bar(ind, queued, width, color='orchid')
            rects2 = ax[plot - 1].bar(ind + width, run, width, color='limegreen')
            rects3 = ax2[plot - 1].bar(ind + width * 2, failed_jobs, width, color='red')
            rects4 = ax[plot - 1].bar(ind + width * 3, fail_queued, width, color='purple')
            rects5 = ax[plot - 1].bar(ind + width * 4, fail_run, width, color='tomato')
            ax[plot - 1].set_ylabel('hours')
            ax2[plot - 1].set_ylabel('# failed jobs')
            ax[plot - 1].set_xticks(ind + width)
            ax[plot - 1].set_xticklabels([job.name for job in joblist[l1:l2]], rotation='vertical')
            ax[plot - 1].set_title(expid, fontsize=20)
            # autolabel(rects1)
            # autolabel(rects2)
            # autolabel(rects4)
            # autolabel(rects5)

            rects6 = ax[plot - 1].plot([0., width * 6 * MAX], [threshold, threshold], "k--", label='wallclock sim')

        for plot in range(1, num_plots + 1):
            ax[plot - 1].set_ylim(0, float(1.10 * max_time))
            ax2[plot - 1].set_yticks(range(0, max_fail + 2))
            ax2[plot - 1].set_ylim(0, max_fail + 1)

        percentage_consumption = timedelta2hours(cpu_consumption) / expected_cpu_consumption * 100
        white = mpatches.Rectangle((0, 0), 0, 0, alpha=0.0)
        totals = ['Period: ' + str(period_ini) + " ~ " + str(period_fi),
                  'Submitted (#): ' + str(total_jobs_submitted),
                  'Run  (#): ' + str(total_jobs_run),
                  'Failed  (#): ' + str(total_jobs_failed),
                  'Completed (#): ' + str(total_jobs_completed),
                  'Expected consumption real (h): ' + str(round(expected_real_consumption, 2)),
                  'Expected consumption CPU time (h): ' + str(round(expected_cpu_consumption, 2)),
                  'Consumption real (h): ' + str(round(timedelta2hours(real_consumption), 2)),
                  'Consumption CPU time (h): ' + str(round(timedelta2hours(cpu_consumption), 2)),
                  'Consumption (%): ' + str(round(percentage_consumption, 2))]
        Log.result('\n'.join(totals))

        ax0 = fig.add_subplot(gs[0, 0])
        ax0.set_frame_on(False)
        ax0.axes.get_xaxis().set_visible(False)
        ax0.axes.get_yaxis().set_visible(False)
        # noinspection PyUnboundLocalVariable
        first_legend = ax0.legend((rects1[0], rects2[0], rects3[0], rects4[0], rects5[0], rects6[0]),
                                  ('Queued (h)', 'Run (h)', 'Failed jobs (#)', 'Fail Queued (h)', 'Fail Run (h)',
                                   'Max wallclock (h)'), loc="upper right")
        plt.gca().add_artist(first_legend)

        ax0.legend([white, white, white, white, white, white, white, white, white, white],
                   totals,
                   handlelength=0,
                   loc="upper left")

        gs.tight_layout(fig, rect=[0, 0.03, 1, 0.97])  # adjust rect parameter while leaving some room for suptitle.
        # plt.show()
        plt.savefig(output_file)

    @staticmethod
    def clean_plot(expid):
        """
        Function to clean space on BasicConfig.LOCAL_ROOT_DIR/plot directory.
        Removes all plots except last two.

        :param expid: experiment's identifier
        :type expid: str
        """
        search_dir = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "plot")
        chdir(search_dir)
        files = filter(path.isfile, listdir(search_dir))
        files = [path.join(search_dir, f) for f in files if 'statistics' not in f]
        files.sort(key=lambda x: path.getmtime(x))
        remain = files[-2:]
        filelist = [f for f in files if f not in remain]
        for f in filelist:
            remove(f)
        Log.result("Plots cleaned!\nLast two plots remanining there.\n")

    @staticmethod
    def clean_stats(expid):
        """
        Function to clean space on BasicConfig.LOCAL_ROOT_DIR/plot directory.
        Removes all stats' plots except last two.

        :param expid: experiment's identifier
        :type expid: str
        """
        search_dir = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "plot")
        chdir(search_dir)
        files = filter(path.isfile, listdir(search_dir))
        files = [path.join(search_dir, f) for f in files if 'statistics' in f]
        files.sort(key=lambda x: path.getmtime(x))
        remain = files[-1:]
        filelist = [f for f in files if f not in remain]
        for f in filelist:
            remove(f)
        Log.result("Stats cleaned!\nLast stats' plot remanining there.\n")
