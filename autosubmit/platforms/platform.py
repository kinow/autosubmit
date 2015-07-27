__author__ = 'jvegas'


class Platform:
    def __init__(self, expid, name):
        self.expid = expid
        self.name = name

    def add_parameters(self, parameters, main_hpc=False):

        if main_hpc:
            prefix = 'HPC'
        else:
            prefix = self.name + '_'

        parameters['{0}ARCH'.format(prefix)] = self.name
        parameters['{0}USER'.format(prefix)] = self.user
        parameters['{0}PROJ'.format(prefix)] = self.project
        parameters['{0}BUDG'.format(prefix)] = self.budget
        parameters['{0}TYPE'.format(prefix)] = self.type
        parameters['{0}SCRATCH_DIR'.format(prefix)] = self.scratch
        parameters['{0}ROOTDIR'.format(prefix)] = self.root_dir
