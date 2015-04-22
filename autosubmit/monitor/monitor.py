#!/usr/bin/env python

# Copyright 2014 Climate Forecasting Unit, IC3

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
        graph = pydotplus.Dot(graph_type='digraph')

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
        for job in joblist:
            if job.has_parents():
                continue

            node_job = pydotplus.Node(job.name, shape='box', style="filled",
                                      fillcolor=self.color_status(job.status))
            exp.add_node(node_job)
            self._add_children(job, exp, node_job)

        graph.add_subgraph(exp)

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

    def generate_output(self, expid, joblist, output_format="pdf"):
        """
        Plots graph for joblist and stores it in a file

        :param expid: experiment's identifier
        :type expid: str
        :param joblist: joblist to plot
        :type joblist: JobList
        :param output_format: file format for plot
        :type output_format: str (png, pdf, ps)
        """
        now = time.localtime()
        output_date = time.strftime("%Y%m%d_%H%M", now)
        output_file = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "plot", expid + "_" + output_date + "." +
                                   output_format)

        graph = self.create_tree_list(expid, joblist)

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

    def generate_output_stats(self, expid, joblist, output_format="pdf"):
        """
        Plots stats for joblist and stores it in a file

        :param expid: experiment's identifier
        :type expid: str
        :param joblist: joblist to plot
        :type joblist: JobList
        :param output_format: file format for plot
        :type output_format: str (png, pdf, ps)
        """
        now = time.localtime()
        output_date = time.strftime("%Y%m%d_%H%M", now)
        output_file = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "plot",  expid + "_statistics_" + output_date +
                                   "." + output_format)
        self.create_bar_diagram(expid, joblist, output_file)

    @staticmethod
    def create_bar_diagram(expid, joblist, output_file):
        """
        Function to plot statistics

        :param expid: experiment's identifier
        :type expid: str
        :param joblist: joblist to plot
        :type joblist: JobList
        :param output_file: path to create file
        :type output_file: str
        """

        def autolabel(rects):
            # attach text labels
            for rect in rects:
                height = rect.get_height()
                if height > max_time:
                    ax[plot - 1].text(rect.get_x() + rect.get_width() / 2., 1.05 * max_time, '%d' % int(height),
                                      ha='center', va='bottom', rotation='vertical', fontsize=9)

        def failabel(rects):
            for rect in rects:
                height = rect.get_height()
                if height > 0:
                    ax[plot - 1].text(rect.get_x() + rect.get_width() / 2., 1 + height, '%d' % int(height), ha='center',
                                      va='bottom', fontsize=9)

        average_run_time = sum([float(job.check_run_time()) / 3600 for job in joblist]) / len(joblist)
        max_time = max(max([float(job.check_run_time()) / 3600 for job in joblist]),
                       max([float(job.check_queued_time()) / 3600 for job in joblist]))
        min_time = min([int(float(job.check_run_time()) / 3600 - average_run_time) for job in joblist])
        # print average_run_time
        # l1 = 0
        # l2 = len(joblist)
        # print [int(job.check_queued_time())/3600 for job in joblist[l1:l2]]
        # print [int(job.check_run_time())/3600 for job in joblist[l1:l2]]
        # print [int(int(job.check_run_time())/3600-average_run_time) for job in joblist[l1:l2]]
        # print [int(job.check_failed_times()) for job in joblist[l1:l2]]

        # These are constants, so they need to be CAPS. Suppress PyCharm warning
        # noinspection PyPep8Naming
        MAX = 12.0
        # noinspection PyPep8Naming
        N = len(joblist)
        num_plots = int(np.ceil(N / MAX))

        ind = np.arange(int(MAX))  # the x locations for the groups
        width = 0.16  # the width of the bars

        plt.close('all')
        fig = plt.figure(figsize=(14, 6 * num_plots))
        # fig = plt.figure()
        ax = []
        lgd = None
        for plot in range(1, num_plots + 1):
            ax.append(fig.add_subplot(num_plots, 1, plot))
            l1 = int((plot - 1) * MAX)
            l2 = int(plot * MAX)
            queued = [float(job.check_queued_time()) / 3600 for job in joblist[l1:l2]]
            run = [float(job.check_run_time()) / 3600 for job in joblist[l1:l2]]
            excess = [float(job.check_run_time()) / 3600 - average_run_time for job in joblist[l1:l2]]
            failed_jobs = [int(job.check_failed_times()) for job in joblist[l1:l2]]
            fail_queued = [float(job.check_fail_queued_time()) / 3600 for job in joblist[l1:l2]]
            fail_run = [float(job.check_fail_run_time()) / 3600 for job in joblist[l1:l2]]
            if plot == num_plots:
                queued = queued + [0] * int(MAX - len(joblist[l1:l2]))
                run = run + [0] * int(MAX - len(joblist[l1:l2]))
                excess = excess + [0] * int(MAX - len(joblist[l1:l2]))
                failed_jobs = failed_jobs + [0] * int(MAX - len(joblist[l1:l2]))
                fail_queued = fail_queued + [0] * int(MAX - len(joblist[l1:l2]))
                fail_run = fail_run + [0] * int(MAX - len(joblist[l1:l2]))
                # ind = np.arange(len([int(job.check_queued_time())/3600 for job in joblist[l1:l2]]))
            rects1 = ax[plot - 1].bar(ind, queued, width, color='r')
            rects2 = ax[plot - 1].bar(ind + width, run, width, color='g')
            rects3 = ax[plot - 1].bar(ind + width * 2, excess, width, color='b')
            rects4 = ax[plot - 1].bar(ind + width * 3, failed_jobs, width, color='y')
            rects5 = ax[plot - 1].bar(ind + width * 4, fail_queued, width, color='m')
            rects6 = ax[plot - 1].bar(ind + width * 5, fail_run, width, color='c')
            ax[plot - 1].set_ylabel('hours')
            ax[plot - 1].set_xticks(ind + width)
            ax[plot - 1].set_xticklabels([job.short_name for job in joblist[l1:l2]], rotation='vertical')
            box = ax[plot - 1].get_position()
            ax[plot - 1].set_position([box.x0, box.y0, box.width * 0.8, box.height * 0.8])
            ax[plot - 1].set_title(expid, fontsize=20, fontweight='bold')
            lgd = ax[plot - 1].legend((rects1[0], rects2[0], rects3[0], rects4[0], rects5[0], rects6[0]), (
                'Queued (h)', 'Run (h)', 'Excess (h)', 'Failed jobs (#)', 'Fail Queued (h)', 'Fail Run (h)'),
                loc="upper left", bbox_to_anchor=(1, 1))
            autolabel(rects1)
            autolabel(rects2)
            failabel(rects4)
            autolabel(rects5)
            autolabel(rects6)
            plt.ylim((1.15 * min_time, 1.15 * max_time))

        # fig.set_size_inches(14,num_plots*6)
        # plt.savefig(output_file, bbox_extra_artists=(lgd), bbox_inches='tight')
        # plt.savefig(output_file, bbox_inches='tight')
        # fig.tight_layout()
        # plt.show()
        plt.subplots_adjust(left=0.1, right=0.8, top=0.97, bottom=0.05, wspace=0.2, hspace=0.6)
        plt.savefig(output_file, bbox_extra_artists=lgd)

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
