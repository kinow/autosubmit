#!/usr/bin/env python

# Copyright 2015-2020 Earth Sciences Department, BSC-CNS
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

from abc import ABCMeta, abstractmethod
import database_managers.database_models as Models

class PlatformInformationHandler():
  def __init__(self, strategy):
    self._strategy = strategy
  
  @property
  def strategy(self):
    return self._strategy
  
  @strategy.setter
  def strategy(self, strategy):
    self._strategy = strategy
  
  def execute_distribution(self, job_data_dc, job_data_dcs_in_wrapper, slurm_monitor):
    result = self._strategy.apply_distribution()
  

class Strategy():
  """ Strategy Interface """
  __metaclass__ = ABCMeta

  @abstractmethod
  def apply_distribution(self, job_data_dc, job_data_dcs_in_wrapper, slurm_monitor):
    pass

  def set_job_data_dc_as_processed(self, job_data_dc, original_ssh_output):
    job_data_dc.platform_output = original_ssh_output
    job_data_dc.row_status = Models.RowStatus.PROCESSED
    return job_data_dc
  
  def get_calculated_weights_of_jobs_in_wrapper(self, job_data_dcs_in_wrapper):
    """ Based on computational weight: running time in seconds * number of cpus. """
    total_weight = sum(job.computational_weight for job in job_data_dcs_in_wrapper)
    return {job.job_name: round(job.computational_weight/total_weight, 4) for job in job_data_dcs_in_wrapper}
  

class SimpleAssociationStrategy(Strategy):
  def apply_distribution(self, job_data_dc, job_data_dcs_in_wrapper, slurm_monitor):
    if len(job_data_dcs_in_wrapper) > 0:
      return []
    job_data_dc.submit = slurm_monitor.header.submit
    job_data_dc.start = slurm_monitor.header.start
    job_data_dc.finish = slurm_monitor.header.finish
    job_data_dc.ncpus = slurm_monitor.header.ncpus
    job_data_dc.nnodes = slurm_monitor.header.nnodes
    job_data_dc.energy = slurm_monitor.header.energy
    job_data_dc.MaxRSS = max(slurm_monitor.header.MaxRSS, slurm_monitor.batch.MaxRSS, slurm_monitor.extern.MaxRSS) # TODO: Improve this rule
    job_data_dc.AveRSS = max(slurm_monitor.header.AveRSS, slurm_monitor.batch.AveRSS, slurm_monitor.extern.AveRSS)        
    job_data_dc = self.set_job_data_dc_as_processed(job_data_dc, slurm_monitor.original_input)
    return [job_data_dc]

class StraightAssociationStrategy(Strategy):
  def apply_distribution(self, job_data_dc, job_data_dcs_in_wrapper, slurm_monitor):
    """ """
    if len(job_data_dcs_in_wrapper) != slurm_monitor.step_count:
      return []
    result = []
    computational_weights = self.get_calculated_weights_of_jobs_in_wrapper(job_data_dcs_in_wrapper)
    for job_dc, step in zip(job_data_dcs_in_wrapper, slurm_monitor.steps):
      job_dc.energy = step.energy + computational_weights.get(job_dc.job_name, 0) * slurm_monitor.extern.energy
      job_dc.AveRSS = step.AveRSS
      job_dc.MaxRSS = step.MaxRSS
      job_dc.platform_output = ""
      result.append(job_dc)
    job_data_dc = self.set_job_data_dc_as_processed(job_data_dc, slurm_monitor.original_input)
    result.append(job_data_dc)
    return result

class GeneralizedDistributionStrategy(Strategy):
  def apply_distribution(self, job_data_dc, job_data_dcs_in_wrapper, slurm_monitor):
    result = []
    computational_weights = self.get_calculated_weights_of_jobs_in_wrapper(job_data_dcs_in_wrapper)
    for job_dc in job_data_dcs_in_wrapper:
      job_dc.energy = computational_weights.get(job_dc.job_name, 0) * slurm_monitor.total_energy
      job_dc.platform_output = ""   
      result.append(job_dc)
    job_data_dc = self.set_job_data_dc_as_processed(job_data_dc, slurm_monitor.original_input)
    result.append(job_data_dc)
    return result

class TwoDimWrapperDistributionStrategy(Strategy):
  def apply_distribution(self, job_data_dc, job_data_dcs_in_wrapper, slurm_monitor):
    result = []        
    # Challenge: Get jobs per level and then distribute energy
    return result

  def get_jobs_per_level(self, job_data_dcs_in_wrapper):
    job_name_to_children_names = {job.job_name:job.children.split(",") for job in job_data_dcs_in_wrapper}
    children_names = []
    for job_name in job_name_to_children_names:
      children_names.extend(job_name_to_children_names[job_name])
    

    
    

    

    



def simple_association_strategy(job_data_dc, slurm_monitor):
  job_data_dc.submit = slurm_monitor.header.submit
  job_data_dc.start = slurm_monitor.header.start
  job_data_dc.finish = slurm_monitor.header.finish
  job_data_dc.ncpus = slurm_monitor.header.ncpus
  job_data_dc.nnodes = slurm_monitor.header.nnodes
  job_data_dc.energy = slurm_monitor.header.energy
  job_data_dc.MaxRSS = max(slurm_monitor.header.MaxRSS, slurm_monitor.batch.MaxRSS, slurm_monitor.extern.MaxRSS) # TODO: Improve this rule
  job_data_dc.AveRSS = max(slurm_monitor.header.AveRSS, slurm_monitor.batch.AveRSS, slurm_monitor.extern.AveRSS)
  job_data_dc.platform_output = slurm_monitor.original_input
  return job_data_dc