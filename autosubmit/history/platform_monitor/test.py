#!/usr/bin/env python3

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

import unittest
from . import platform_utils as utils
from .slurm_monitor import SlurmMonitor

class TestSlurmMonitor(unittest.TestCase):
  def test_reader_on_simple_wrapper_example_1(self):
    ssh_output = utils.read_example("wrapper1.txt")
    slurm_monitor = SlurmMonitor(ssh_output)      
    # Header
    self.assertTrue(slurm_monitor.input_items[0].is_batch is False)
    self.assertTrue(slurm_monitor.input_items[0].is_detail is False)
    self.assertTrue(slurm_monitor.input_items[0].is_extern is False)
    self.assertTrue(slurm_monitor.input_items[0].is_header is True)
    self.assertTrue(slurm_monitor.input_items[0].is_detail is False)
    # Batch
    self.assertTrue(slurm_monitor.input_items[1].is_batch is True)
    self.assertTrue(slurm_monitor.input_items[1].is_detail is True)
    self.assertTrue(slurm_monitor.input_items[1].is_extern is False)
    self.assertTrue(slurm_monitor.input_items[1].is_header is False)
    self.assertTrue(slurm_monitor.input_items[1].is_detail is True)
    # Extern
    self.assertTrue(slurm_monitor.input_items[2].is_batch is False)
    self.assertTrue(slurm_monitor.input_items[2].is_detail is True)
    self.assertTrue(slurm_monitor.input_items[2].is_extern is True)
    self.assertTrue(slurm_monitor.input_items[2].is_header is False)
    self.assertTrue(slurm_monitor.input_items[2].is_detail is True)
    header = slurm_monitor.header
    batch = slurm_monitor.batch
    extern = slurm_monitor.extern
    self.assertIsNotNone(header)
    self.assertIsNotNone(batch)
    self.assertIsNotNone(extern)
    # print("{0} {1} <- {2}".format(batch.name, batch.energy, batch.energy_str))
    # print("{0} {1} <- {2}".format(extern.name, extern.energy, extern.energy_str))
    # print("{0} {1} <- {2}".format(header.name, header.energy, header.energy_str))
    self.assertTrue(slurm_monitor.steps_plus_extern_approximate_header_energy())

  
  def test_reader_on_simple_wrapper_example_2(self):  
    ssh_output = utils.read_example("wrapper2.txt") # not real
    slurm_monitor = SlurmMonitor(ssh_output)         
    # Header
    self.assertTrue(slurm_monitor.input_items[0].is_batch is False)
    self.assertTrue(slurm_monitor.input_items[0].is_detail is False)
    self.assertTrue(slurm_monitor.input_items[0].is_step is False)
    self.assertTrue(slurm_monitor.input_items[0].is_extern is False)
    self.assertTrue(slurm_monitor.input_items[0].is_header is True)
    # Batch
    self.assertTrue(slurm_monitor.input_items[1].is_batch is True)
    self.assertTrue(slurm_monitor.input_items[1].is_detail is True)
    self.assertTrue(slurm_monitor.input_items[1].is_step is False)
    self.assertTrue(slurm_monitor.input_items[1].is_extern is False)
    self.assertTrue(slurm_monitor.input_items[1].is_header is False)
    # Step 0
    self.assertTrue(slurm_monitor.input_items[2].is_batch is False)
    self.assertTrue(slurm_monitor.input_items[2].is_detail is True)
    self.assertTrue(slurm_monitor.input_items[2].is_step is True)
    self.assertTrue(slurm_monitor.input_items[2].is_extern is False)
    self.assertTrue(slurm_monitor.input_items[2].is_header is False)
    self.assertTrue(slurm_monitor.input_items[2].step_number >= 0)
  
  def test_reader_on_big_wrapper(self):
    ssh_output = utils.read_example("wrapper_big.txt")
    slurm_monitor = SlurmMonitor(ssh_output)
    self.assertTrue(slurm_monitor.step_count == 30)
    header = slurm_monitor.header
    batch = slurm_monitor.batch
    extern = slurm_monitor.extern
    self.assertIsNotNone(header)
    self.assertIsNotNone(batch)
    self.assertIsNotNone(extern)    
    self.assertTrue(slurm_monitor.steps_plus_extern_approximate_header_energy())
    

if __name__ == '__main__':
  unittest.main()