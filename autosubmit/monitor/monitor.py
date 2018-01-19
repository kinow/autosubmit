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
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches

import subprocess

from autosubmit.job.job_common import Status
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.config.config_common import AutosubmitConfig
from bscearth.utils.log import Log
from bscearth.utils.config_parser import ConfigParserFactory

from diagram import create_bar_diagram


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

    def create_tree_list(self, expid, joblist, packages, groups):
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
        legend.add_node(pydotplus.Node(name='UNKNOWN', shape='box', style="",
                                       fillcolor=self._table[Status.UNKNOWN]))
        legend.add_node(pydotplus.Node(name='WAITING', shape='box', style="filled",
                                       fillcolor=self._table[Status.WAITING]))
        legend.add_node(pydotplus.Node(name='READY', shape='box', style="filled",
                                       fillcolor=self._table[Status.READY]))
        legend.add_node(pydotplus.Node(name='SUBMITTED', shape='box', style="filled",
                                       fillcolor=self._table[Status.SUBMITTED]))
        legend.add_node(pydotplus.Node(name='QUEUING', shape='box', style="filled",
                                       fillcolor=self._table[Status.QUEUING]))
        legend.add_node(pydotplus.Node(name='RUNNING', shape='box', style="filled",
                                       fillcolor=self._table[Status.RUNNING]))
        legend.add_node(pydotplus.Node(name='COMPLETED', shape='box', style="filled",
                                       fillcolor=self._table[Status.COMPLETED]))
        legend.add_node(pydotplus.Node(name='FAILED', shape='box', style="filled",
                                       fillcolor=self._table[Status.FAILED]))
        legend.add_node(pydotplus.Node(name='SUSPENDED', shape='box', style="filled",
                                       fillcolor=self._table[Status.SUSPENDED]))
        graph.add_subgraph(legend)

        exp = pydotplus.Subgraph(graph_name='Experiment', label=expid)
        self.nodes_ploted = set()
        Log.debug('Creating job graph...')

        jobs_packages_dict = dict()
        if packages != None and packages:
            for (exp_id, package_name, job_name) in packages:
                jobs_packages_dict[job_name] = package_name

        packages_subgraphs_dict = dict()

        for job in joblist:
            if job.has_parents():
                continue

            if not groups or job.name not in groups['jobs'] or (job.name in groups['jobs'] and len(groups['jobs'][job.name]) == 1):
                node_job = pydotplus.Node(job.name, shape='box', style="filled",
                                          fillcolor=self.color_status(job.status))
                if groups and job.name in groups['jobs']:
                    group = groups['jobs'][job.name][0]
                    node_job.obj_dict['name'] = group
                    node_job.obj_dict['attributes']['fillcolor'] = self.color_status(groups['status'][group])
                    node_job.obj_dict['attributes']['shape'] = 'box3d'
                exp.add_node(node_job)
                self._add_children(job, exp, node_job, groups)

        if groups:
            for job, group in groups['jobs'].items():
                if len(group) > 1:
                    subgraph = pydotplus.graphviz.Cluster(graph_name='cluster_'+'_'.join(group))
                    subgraph.obj_dict['attributes']['color'] = 'invis'

                    previous_node = exp.get_node(group[0])[0]
                    subgraph.add_node(previous_node)

                    for i in range(1, len(group)):
                        node = exp.get_node(group[i])[0]
                        subgraph.add_node(node)
                        # constraint false allows the horizontal alignment
                        edge = pydotplus.Edge(previous_node, node, constraint='false', penwidth=4)
                        edge.obj_dict['attributes']['dir'] = 'none'
                        subgraph.add_edge(edge)
                        previous_node = node
                    graph.add_subgraph(subgraph)
            graph.set_strict(True)

        graph.add_subgraph(exp)

        for node in exp.get_nodes():
            name = node.obj_dict['name']
            if name in jobs_packages_dict:
                package = jobs_packages_dict[name]
                if package not in packages_subgraphs_dict:
                    packages_subgraphs_dict[package] = pydotplus.graphviz.Cluster(graph_name=package)
                    packages_subgraphs_dict[package].obj_dict['attributes']['color'] = 'black'
                    packages_subgraphs_dict[package].obj_dict['attributes']['style'] = 'dashed'
                packages_subgraphs_dict[package].add_node(node)

        for package, cluster in packages_subgraphs_dict.items():
            graph.add_subgraph(cluster)

        Log.debug('Graph definition finalized')
        return graph

    def _add_children(self, job, exp, node_job, groups):
        if job in self.nodes_ploted:
            return
        self.nodes_ploted.add(job)
        if job.has_children() != 0:
            for child in sorted(job.children, key=lambda k: k.name):
                if groups and child.name in groups['jobs']:
                    node_child = exp.get_node(groups['jobs'][child.name][0])
                else:
                    node_child = exp.get_node(child.name)
                if len(node_child) == 0:
                    flag = True
                    if groups and child.name in groups['jobs'] and len(groups['jobs'][child.name]) == 1:
                        group = groups['jobs'][child.name][0]
                        node_child = pydotplus.Node(group, shape='box3d', style="filled", fillcolor=self.color_status(groups['status'][group]))
                    elif not groups or child.name not in groups['jobs']:
                        node_child = pydotplus.Node(child.name, shape='box', style="filled",
                                                    fillcolor=self.color_status(child.status))
                    exp.add_node(node_child)
                    exp.add_edge(pydotplus.Edge(node_job, node_child))
                else:
                    node_child = node_child[0]
                    exp.add_edge(pydotplus.Edge(node_job, node_child))
                    flag = False
                if flag:
                    self._add_children(child, exp, node_child, groups)

    def generate_output(self, expid, joblist, path, output_format="pdf", packages=None, show=False, groups=dict()):
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

        graph = self.create_tree_list(expid, joblist, packages, groups)

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

        self.generate_output_txt(expid, joblist, path)

    def generate_output_txt(self, expid, joblist, path):
        Log.info('Writing status txt...')

        now = time.localtime()
        output_date = time.strftime("%Y%m%d_%H%M", now)
        file_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "status", expid + "_" + output_date + ".txt")

        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

        output_file = open(file_path, 'w+')
        for job in joblist:
            log_out = job.local_logs[0]
            log_err = job.local_logs[1]

            output = job.name + " " + Status().VALUE_TO_KEY[job.status] + " " + path + "/" + log_out + " " + path + "/" + log_err + "\n"
            output_file.write(output)
        output_file.close()

        Log.result('Status txt created at {0}', output_file)

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
        create_bar_diagram(expid, joblist, self.get_general_stats(expid), output_file, period_ini, period_fi)
        Log.result('Stats created at {0}', output_file)
        if show:
            try:
                subprocess.check_call(['xdg-open', output_file])
            except subprocess.CalledProcessError:
                Log.error('File {0} could not be opened', output_file)

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

    @staticmethod
    def get_general_stats(expid):
        general_stats = []
        general_stats_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, expid, "tmp", expid + "_GENERAL_STATS")
        parser = AutosubmitConfig.get_parser(ConfigParserFactory(), general_stats_path)
        for section in parser.sections():
            general_stats.append((section, ''))
            general_stats += parser.items(section)
        return general_stats
