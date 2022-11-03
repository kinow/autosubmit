#!/usr/bin/env python3

# Copyright 2017-2020 Earth Sciences Department, BSC-CNS

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

import traceback
import numpy as np
import matplotlib as mtp

mtp.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
# from autosubmit.experiment.statistics import ExperimentStats
from autosubmit.statistics.statistics import Statistics
from autosubmit.job.job import Job
from log.log import Log, AutosubmitCritical
from datetime import datetime
from typing import Dict, List

Log.get_logger("Autosubmit")

# Autosubmit stats constants
RATIO = 4
MAX_JOBS_PER_PLOT = 12.0
MAX_NUM_PLOTS = 40


def create_bar_diagram(experiment_id, jobs_list, general_stats, output_file, period_ini=None, period_fi=None,
                       queue_time_fixes=None):
    # type: (str, List[Job], List[str], str, datetime, datetime, Dict[str, int]) -> None
    """
    Creates a bar diagram of the statistics.

    :param queue_time_fixes:
    :param experiment_id: experiment's identifier
    :type experiment_id: str
    :param jobs_list: list of jobs
    :type jobs_list: List[Job]

    :param general_stats: list of sections and options in the %DEFAULT.EXPID%_GENERAL_STATS file
    :type general_stats: list of tuples  
    :param output_file: path to the output file  
    :type output_file: str  
    :param period_ini: starting date and time
    :type period_ini: datetime  
    :param period_fi: finish date and time
    :type period_fi: datetime  
    """
    # Error prevention
    plt.close('all')
    normal_plots_count = 0
    failed_jobs_plots_count = 0
    exp_stats = None
    try:
        exp_stats = Statistics(jobs_list, period_ini, period_fi, queue_time_fixes)
        exp_stats.calculate_statistics()
        exp_stats.calculate_summary()
        exp_stats.make_old_format()

        failed_jobs_dict = exp_stats.build_failed_jobs_only_list()
        # Stats variables definition
        normal_plots_count = int(np.ceil(len(exp_stats.jobs_stat) / MAX_JOBS_PER_PLOT))
        failed_jobs_plots_count = int(np.ceil(len(failed_jobs_dict) / MAX_JOBS_PER_PLOT))
    except Exception as exp:
        print(exp)
        print((traceback.format_exc()))

    # Plotting
    total_plots_count = normal_plots_count + failed_jobs_plots_count
    # num_plots = norma 
    # ind = np.arrange(int(MAX_JOBS_PER_PLOT))
    width = 0.16
    # Creating stats figure + sanity check
    if total_plots_count > MAX_NUM_PLOTS:
        message = "The results are too large to be shown, try narrowing your query. \n Use a filter like -ft where you supply a list of job types, e.g. INI, SIM; \
        or -fp where you supply an integer that represents the number of hours into the past that should be queried: \
        suppose it is noon, if you supply -fp 5 the query will consider changes starting from 7:00 am. If you really wish to query the whole experiment, refer to Autosubmit GUI."
        Log.info(message)
        raise AutosubmitCritical("Stats query out of bounds", 7061, message)

    fig = plt.figure(figsize=(RATIO * 4, 3 * RATIO * total_plots_count))

    fig.suptitle('STATS - ' + experiment_id, fontsize=24, fontweight='bold')
    # Variables initialization
    ax, ax2 = [], []
    rects = [None] * 5
    # print("Normal plots: {}".format(normal_plots_count))
    # print("Failed jobs plots: {}".format(failed_jobs_plots_count))
    # print("Total plots: {}".format(total_plots_count))
    grid_spec = gridspec.GridSpec(RATIO * total_plots_count + 2, 1)
    i_plot = 0
    for plot in range(1, normal_plots_count + 1):
        try:
            # Calculating jobs inside the given plot
            l1 = int((plot - 1) * MAX_JOBS_PER_PLOT)
            l2 = min(int(plot * MAX_JOBS_PER_PLOT), len(exp_stats.jobs_stat))
            if l2 - l1 <= 0:
                continue
            ind = np.arange(l2 - l1)
            # Building plot axis
            ax.append(fig.add_subplot(grid_spec[RATIO * plot - RATIO + 2:RATIO * plot + 1]))
            ax[plot - 1].set_ylabel('hours')
            ax[plot - 1].set_xticks(ind + width)
            ax[plot - 1].set_xticklabels(
                [job.name for job in jobs_list[l1:l2]], rotation='vertical')
            ax[plot - 1].set_title(experiment_id, fontsize=20)
            upper_limit = round(1.10 * exp_stats.max_time, 4)
            ax[plot - 1].set_yticks(np.arange(0, upper_limit, round(upper_limit / 10, 4)))
            ax[plot - 1].set_ylim(0, float(1.10 * exp_stats.max_time))
            # Building reacts
            rects[0] = ax[plot - 1].bar(ind, exp_stats.queued[l1:l2], width, color='lightpink')
            rects[1] = ax[plot - 1].bar(ind + width, exp_stats.run[l1:l2], width, color='green')
            rects[2] = ax[plot - 1].bar(ind + width * 3, exp_stats.fail_queued[l1:l2], width, color='lightsalmon')
            rects[3] = ax[plot - 1].bar(ind + width * 4, exp_stats.fail_run[l1:l2], width, color='salmon')
            rects[4] = ax[plot - 1].plot([0., width * 6 * MAX_JOBS_PER_PLOT],
                                         [exp_stats.threshold, exp_stats.threshold], "k--", label='wallclock sim')
            i_plot = plot
        except Exception as exp:
            print((traceback.format_exc()))
            print(exp)

    job_names_in_failed = [name for name in exp_stats.failed_jobs_dict]
    failed_jobs_rects = [None]
    for j_plot in range(1, failed_jobs_plots_count + 1):
        try:
            l1 = int((j_plot - 1) * MAX_JOBS_PER_PLOT)
            l2 = min(int(j_plot * MAX_JOBS_PER_PLOT), len(job_names_in_failed))
            if l2 - l1 <= 0:
                continue
            ind = np.arange(l2 - l1)
            plot = i_plot + j_plot
            ax.append(fig.add_subplot(grid_spec[RATIO * plot - RATIO + 2:RATIO * plot + 1]))
            ax[plot - 1].set_ylabel('# failed attempts')
            ax[plot - 1].set_xticks(ind + width)
            ax[plot - 1].set_xticklabels([name for name in job_names_in_failed[l1:l2]], rotation='vertical')
            ax[plot - 1].set_title(experiment_id, fontsize=20)
            ax[plot - 1].set_ylim(0, float(1.10 * exp_stats.max_fail))
            ax[plot - 1].set_yticks(range(0, exp_stats.max_fail + 2))
            failed_jobs_rects[0] = ax[plot - 1].bar(ind + width * 2, [exp_stats.failed_jobs_dict[name] for name in
                                                                      job_names_in_failed[l1:l2]], width, color='red')
        except Exception as exp:
            print((traceback.format_exc()))
            print(exp)

    # Building legends subplot
    legends_plot = fig.add_subplot(grid_spec[0, 0])
    legends_plot.set_frame_on(False)
    legends_plot.axes.get_xaxis().set_visible(False)
    legends_plot.axes.get_yaxis().set_visible(False)

    try:
        # Building legends
        # print("Legends")
        build_legends(legends_plot, rects, exp_stats, general_stats)

        # Saving output figure
        grid_spec.tight_layout(fig, rect=[0, 0.03, 1, 0.97])
        plt.savefig(output_file)

        create_csv_stats(exp_stats, jobs_list, output_file)
    except Exception as exp:
        print(exp)
        print((traceback.format_exc()))


def create_csv_stats(exp_stats, jobs_list, output_file):
    job_names = [job.name for job in exp_stats.jobs_stat]
    start_times = exp_stats.start_times
    end_times = exp_stats.end_times
    queuing_times = exp_stats.queued
    running_times = exp_stats.run

    output_file = output_file.replace('pdf', 'csv')
    with open(output_file, 'w') as file:
        file.write(
            "Job,Started,Ended,Queuing time (hours),Running time (hours)\n")
        for i in range(len(jobs_list)):
            file.write("{0},{1},{2},{3},{4}\n".format(
                job_names[i], start_times[i], end_times[i], queuing_times[i], running_times[i]))


def build_legends(plot, rects, experiment_stats, general_stats):
    # type: (plt.figure, List[plt.bar], Statistics, List[str]) -> None
    # Main legend with colourful rectangles
    legend_rects = [[rect[0] for rect in rects]]
    legend_titles = [
        ['Queued (h)', 'Run (h)', 'Fail Queued (h)', 'Fail Run (h)', 'Max wallclock (h)']
    ]
    legend_locs = ["upper right"]
    legend_handlelengths = [None]

    # General stats legends, if exists
    if len(general_stats) > 0:
        legend_rects.append(get_whites_array(len(general_stats)))
        legend_titles.append([str(key) + ': ' + str(value) for key, value in general_stats])
        legend_locs.append("upper center")
        legend_handlelengths.append(0)

    # Total stats legend
    stats_summary_as_list = experiment_stats.get_summary_as_list()
    legend_rects.append(get_whites_array(len(stats_summary_as_list)))
    legend_titles.append(stats_summary_as_list)
    legend_locs.append("upper left")
    legend_handlelengths.append(0)

    # Creating the legends
    legends = create_legends(plot, legend_rects, legend_titles, legend_locs, legend_handlelengths)
    for legend in legends:
        plt.gca().add_artist(legend)


def create_legends(plot, rects, titles, locs, handlelengths):
    legends = []
    for i in range(len(rects)):
        legends.append(create_legend(
            plot, rects[i], titles[i], locs[i], handlelengths[i]))
    return legends


def create_legend(plot, rects, titles, loc, handlelength=None):
    return plot.legend(rects, titles, loc=loc, handlelength=handlelength)


def get_whites_array(length):
    white = mpatches.Rectangle((0, 0), 0, 0, alpha=0.0)
    return [white for _ in range(length)]
