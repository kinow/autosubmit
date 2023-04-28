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

from autosubmit.platforms.wrappers.wrapper_builder import WrapperDirector, PythonVerticalWrapperBuilder, \
    PythonHorizontalWrapperBuilder, PythonHorizontalVerticalWrapperBuilder, PythonVerticalHorizontalWrapperBuilder, \
    BashHorizontalWrapperBuilder, BashVerticalWrapperBuilder, SrunHorizontalWrapperBuilder,SrunVerticalHorizontalWrapperBuilder
from autosubmitconfigparser.config.configcommon import AutosubmitConfig


class WrapperFactory(object):

    def __init__(self, platform):
        self.as_conf = None
        self.platform = platform
        self.wrapper_director = WrapperDirector()
        self.exception = "This type of wrapper is not supported for this platform"

    def get_wrapper(self, wrapper_builder, **kwargs):
        wrapper_data = self.as_conf.experiment_data["CURRENT_WRAPPER"]
        kwargs['allocated_nodes'] = self.allocated_nodes()
        kwargs['dependency'] = self.dependency(kwargs['dependency'])
        kwargs['queue'] = self.queue(kwargs['queue'])
        kwargs['partition'] = self.partition(wrapper_data['PARTITION'])
        kwargs["exclusive"] = self.exclusive(wrapper_data['EXCLUSIVE'])
        kwargs["custom_directives"] = self.custom_directives(wrapper_data["CUSTOM_DIRECTIVES"])
        kwargs["executable"] = wrapper_data["EXECUTABLE"]
        kwargs['header_directive'] = self.header_directives(**kwargs)
        builder = wrapper_builder(**kwargs)
        return self.wrapper_director.construct(builder)

    def vertical_wrapper(self, **kwargs):
        raise NotImplemented(self.exception)

    def horizontal_wrapper(self, **kwargs):
        raise NotImplemented(self.exception)

    def hybrid_wrapper_horizontal_vertical(self, **kwargs):
        raise NotImplemented(self.exception)

    def hybrid_wrapper_vertical_horizontal(self, **kwargs):
        raise NotImplemented(self.exception)

    def header_directives(self, **kwargs):
        pass

    def allocated_nodes(self):
        return ''

    def dependency(self, dependency):
        return '#' if dependency is None else self.dependency_directive(dependency)
    def queue(self, queue):
        return '#' if not queue else self.queue_directive(queue)
    def partition(self, partition):
        return '#' if not partition else self.partition_directive(partition)
    def exclusive(self, exclusive):
        return '#' if not exclusive or str(exclusive).lower() == "false" else self.exclusive_directive(exclusive)
    def custom_directives(self, custom_directives):
        return '#' if not custom_directives else self.get_custom_directives(custom_directives)
    def get_custom_directives(self, custom_directives):
        """
        Returns custom directives for the specified job
        :param job: Job object
        :return: String with custom directives
        """
        # There is no custom directives, so directive is empty
        if custom_directives != '':
            return '\n'.join(str(s) for s in custom_directives)
        return ""

    def dependency_directive(self, dependency):
        pass
    def queue_directive(self, queue):
        pass
    def partition_directive(self, partition):
        pass
    def exclusive_directive(self, exclusive):
        pass




class SlurmWrapperFactory(WrapperFactory):

    def vertical_wrapper(self, **kwargs):
        return PythonVerticalWrapperBuilder(**kwargs)

    def horizontal_wrapper(self, **kwargs):

        if kwargs["method"] == 'srun':
            return SrunHorizontalWrapperBuilder(**kwargs)
        else:
            return PythonHorizontalWrapperBuilder(**kwargs)

    def hybrid_wrapper_horizontal_vertical(self, **kwargs):
        return PythonHorizontalVerticalWrapperBuilder(**kwargs)

    def hybrid_wrapper_vertical_horizontal(self, **kwargs):
        if kwargs["method"] == 'srun':
            return SrunVerticalHorizontalWrapperBuilder(**kwargs)
        else:
            return PythonVerticalHorizontalWrapperBuilder(**kwargs)

    def header_directives(self, **kwargs):
        return self.platform.wrapper_header(**kwargs)

    def allocated_nodes(self):
        return self.platform.allocated_nodes()

    def dependency_directive(self, dependency):
        return '#SBATCH --dependency=afterok:{0}'.format(dependency)

    def queue_directive(self, queue):
        return '#SBATCH --qos={0}'.format(queue)

    def partition_directive(self, partition):
        return '#SBATCH --partition={0}'.format(partition)
    def exclusive_directive(self, exclusive):
        return '#SBATCH --exclusive'


class LSFWrapperFactory(WrapperFactory):

    def vertical_wrapper(self, **kwargs):
        return PythonVerticalWrapperBuilder(**kwargs)

    def horizontal_wrapper(self, **kwargs):
        return PythonHorizontalWrapperBuilder(**kwargs)

    def header_directives(self, **kwargs):
        return self.platform.wrapper_header(**kwargs)

    def queue_directive(self, queue):
        return queue

    def dependency_directive(self, dependency):
        return '#BSUB -w \'done({0})\' [-ti]'.format(dependency)


class EcWrapperFactory(WrapperFactory):

    def vertical_wrapper(self, **kwargs):
        return BashVerticalWrapperBuilder(**kwargs)

    def horizontal_wrapper(self, **kwargs):
        return BashHorizontalWrapperBuilder(**kwargs)

    def header_directives(self, **kwargs):
        return self.platform.wrapper_header(**kwargs)

    def queue_directive(self, queue):
        return queue

    def dependency_directive(self, dependency):
        return '#PBS -v depend=afterok:{0}'.format(dependency)

class PJMWrapperFactory(WrapperFactory):

    def vertical_wrapper(self, **kwargs):
        return PythonVerticalWrapperBuilder(**kwargs)

    def horizontal_wrapper(self, **kwargs):

        if kwargs["method"] == 'srun':
            return SrunHorizontalWrapperBuilder(**kwargs)
        else:
            return PythonHorizontalWrapperBuilder(**kwargs)

    def hybrid_wrapper_horizontal_vertical(self, **kwargs):
        return PythonHorizontalVerticalWrapperBuilder(**kwargs)

    def hybrid_wrapper_vertical_horizontal(self, **kwargs):
        if kwargs["method"] == 'srun':
            return SrunVerticalHorizontalWrapperBuilder(**kwargs)
        else:
            return PythonVerticalHorizontalWrapperBuilder(**kwargs)

    def header_directives(self, **kwargs):
        return self.platform.wrapper_header(**kwargs)

    def allocated_nodes(self):
        return self.platform.allocated_nodes()

    #def dependency_directive(self, dependency):
    #    # There is no option for afterok in the PJM scheduler, but I think it is not needed.
    #    return '#PJM --dependency=afterok:{0}'.format(dependency)

    def queue_directive(self, queue):
        return '#PJM -L rscgrp={0}'.format(queue)

    def partition_directive(self, partition):
        return '#PJM -g {0}'.format(partition)
