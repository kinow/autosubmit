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

from os import path
import os
from shutil import rmtree
import subprocess
import shutil
import zipfile
#from autosubmit import Autosubmit
from autosubmit.config.basicConfig import BasicConfig
from time import time
from log.log import Log, AutosubmitCritical, AutosubmitError
Log.get_logger("Autosubmit")


class AutosubmitGit:
    """
    Class to handle experiment git repository

    :param expid: experiment identifier
    :type expid: str
    """

    def __init__(self, expid):
        self._expid = expid

    @staticmethod
    def clean_git(as_conf):
        """
        Function to clean space on BasicConfig.LOCAL_ROOT_DIR/git directory.

        :param as_conf: experiment configuration
        :type as_conf: autosubmit.config.AutosubmitConfig
        """
        proj_dir = os.path.join(
            BasicConfig.LOCAL_ROOT_DIR, as_conf.expid, BasicConfig.LOCAL_PROJ_DIR)
        dirname_path = as_conf.get_project_dir()
        Log.debug("Checking git directory status...")
        if path.isdir(dirname_path):
            if path.isdir(os.path.join(dirname_path, '.git')):
                try:
                    output = subprocess.check_output("cd {0}; git diff-index HEAD --".format(dirname_path),
                                                     shell=True)
                except subprocess.CalledProcessError as e:
                    raise AutosubmitCritical(
                        "Failed to retrieve git info ...", 7064, e.message)
                if output:
                    Log.info("Changes not committed detected... SKIPPING!")
                    raise AutosubmitCritical("Commit needed!", 7013)
                else:
                    output = subprocess.check_output("cd {0}; git log --branches --not --remotes".format(dirname_path),
                                                     shell=True)
                    if output:
                        Log.info("Changes not pushed detected... SKIPPING!")
                        raise AutosubmitCritical(
                            "Synchronization needed!", 7064)
                    else:
                        if not as_conf.set_git_project_commit(as_conf):
                            return False
                        Log.debug("Removing directory")
                        rmtree(proj_dir)
            else:
                Log.debug("Not a git repository... SKIPPING!")
        else:
            Log.debug("Not a directory... SKIPPING!")
        return True

    @staticmethod
    def check_commit(as_conf):
        """
        Function to check uncommited changes

        :param as_conf: experiment configuration
        :type as_conf: autosubmit.config.AutosubmitConfig
        """
        proj_dir = os.path.join(
            BasicConfig.LOCAL_ROOT_DIR, as_conf.expid, BasicConfig.LOCAL_PROJ_DIR)
        dirname_path = as_conf.get_project_dir()
        if path.isdir(dirname_path):
            Log.debug("Checking git directory status...")
            if path.isdir(os.path.join(dirname_path, '.git')):
                try:
                    output = subprocess.check_output("cd {0}; git diff-index HEAD --".format(dirname_path),
                                                     shell=True)
                except subprocess.CalledProcessError:
                    Log.info("This is not a git experiment")
                    return True

                if output:
                    Log.printlog(
                        "There are local changes not commited to git", 3000)
                    return True
                else:
                    output = subprocess.check_output("cd {0}; git log --branches --not --remotes".format(dirname_path),
                                                     shell=True)
                    if output:
                        Log.printlog(
                            "There are local changes not pushed to git", 3000)
                        return True
                    else:
                        Log.info("Model Git repository is updated")
                        Log.result("Model Git repository is updated")

        return True

    @staticmethod
    def clone_repository(as_conf, force, hpcarch):
        """
        Clones a specified git repository on the project folder

        :param as_conf: experiment configuration
        :type as_conf: autosubmit.config.AutosubmitConfig
        :param force: if True, it will overwrite any existing clone
        :type force: bool
        :param hpcarch: current main platform
        :type force: bool
        :return: True if clone was successful, False otherwise
        """
        submodule_failure = False

        if not as_conf.is_valid_git_repository():
            raise AutosubmitCritical(
                "Incorrect git Configuration, check origin,commit and branch settings of expdef file", 7064)
        git_project_origin = as_conf.get_git_project_origin()
        git_project_branch = as_conf.get_git_project_branch()
        git_remote_project_path = as_conf.get_git_remote_project_root()

        if git_project_branch == '':
            git_project_branch = 'master'
        git_project_commit = as_conf.get_git_project_commit()
        git_project_submodules = as_conf.get_submodules_list()
        if as_conf.get_fetch_single_branch() != "true":
            git_single_branch = False
        else:
            git_single_branch = True
        project_destination = as_conf.get_project_destination()
        project_path = os.path.join(
            BasicConfig.LOCAL_ROOT_DIR, as_conf.expid, BasicConfig.LOCAL_PROJ_DIR)
        project_backup_path = os.path.join(
            BasicConfig.LOCAL_ROOT_DIR, as_conf.expid, 'proj_{0}'.format(int(time())))
        git_path = as_conf.get_project_dir()

        # Making proj backup
        if force:
            if os.path.exists(project_path):
                Log.info("Making a backup of your current proj folder at {0}".format(
                    project_backup_path))
                shutil.move(project_path, project_backup_path)
            #shutil.make_archive(project_backup_path, 'zip', project_path)
            #project_backup_path = project_backup_path + ".zip"

        if os.path.exists(project_path):
            Log.info("Using project folder: {0}", project_path)
            # print("Force {0}".format(force))
            if not force:
                Log.debug("The project folder exists. SKIPPING...")
                return True
            else:
                shutil.rmtree(project_path)
        os.mkdir(project_path)
        Log.debug("The project folder {0} has been created.", project_path)

        if git_remote_project_path != '':
            if git_remote_project_path[-1] == '/':
                git_remote_path = os.path.join(
                    git_remote_project_path[:-1], as_conf.expid, BasicConfig.LOCAL_PROJ_DIR)
            else:
                git_remote_path = os.path.join(
                    git_remote_project_path, as_conf.expid, BasicConfig.LOCAL_PROJ_DIR)
            project_path = git_remote_path

        if git_project_commit:
            Log.info("Fetching {0} into {1}", git_project_commit +
                     " " + git_project_origin, project_path)
            try:
                if git_single_branch:
                    command = "cd {0}; git clone  {1} {4}; cd {2}; git checkout {3};".format(project_path,
                                                                                             git_project_origin, git_path,
                                                                                             git_project_commit,
                                                                                             project_destination)
                else:
                    command = "cd {0}; git clone {1} {4}; cd {2}; git checkout {3};".format(project_path,
                                                                                            git_project_origin, git_path,
                                                                                            git_project_commit,
                                                                                            project_destination)
                if git_project_submodules.__len__() <= 0:
                    command += " git submodule update --init --recursive"
                else:
                    command += " cd {0}; git submodule init;".format(
                        project_destination)
                    for submodule in git_project_submodules:
                        try:
                            command += " git submodule update {0};".format(
                                submodule)
                        except BaseException as e:
                            submodule_failure = True
                            Log.printlog("Trace: {0}".format(e.message), 6014)
                            Log.printlog(
                                "Submodule {0} has a wrong configuration".format(submodule), 6014)
                if git_remote_project_path == '':
                    output = subprocess.check_output(command, shell=True)
                else:

                    command = "cd {0} && {1}".format(git_remote_path, command)
                    hpcarch.send_command(command)
            except subprocess.CalledProcessError as e:
                shutil.rmtree(project_path)
                if os.path.exists(project_backup_path):
                    Log.info("Restoring proj folder...")
                    shutil.move(project_backup_path, project_path)
                raise AutosubmitCritical(
                    "Can not checkout commit {0}: {1}".format(git_project_commit, output))
        else:
            Log.info("Cloning {0} into {1}", git_project_branch +
                     " " + git_project_origin, project_path)
            try:
                command = "cd {0}; ".format(project_path)

                if git_project_submodules.__len__() <= 0:
                    if not git_single_branch:
                        command += " git clone --recursive -b {0} {1} {2}".format(git_project_branch, git_project_origin,
                                                                                  project_destination)
                    else:
                        command += " git clone --single-branch  --recursive -b {0} {1} {2}".format(git_project_branch, git_project_origin,
                                                                                                   project_destination)
                else:
                    if not git_single_branch:
                        command += " git clone -b {0} {1} {2};".format(git_project_branch, git_project_origin,
                                                                       project_destination)
                    else:
                        command += " git clone --single-branch -b {0} {1} {2};".format(git_project_branch,
                                                                                       git_project_origin,
                                                                                       project_destination)

                    command += " cd {0}; git submodule init;".format(
                        project_destination)
                    for submodule in git_project_submodules:
                        try:
                            command += " git submodule update  {0};".format(
                                submodule)
                        except BaseException as e:
                            submodule_failure = True
                            Log.printlog("Trace: {0}".format(e.message), 6014)
                            Log.printlog(
                                "Submodule {0} has a wrong configuration".format(submodule), 6014)
                Log.debug('{0}', command)
                if git_remote_project_path == '':
                    output = subprocess.check_output(command, shell=True)
                else:
                    hpcarch.send_command(command)

            except subprocess.CalledProcessError as e:
                shutil.rmtree(project_path)
                if os.path.exists(project_backup_path):
                    Log.info("Restoring proj folder...")
                    shutil.move(project_backup_path, project_path)
                raise AutosubmitCritical("Can not clone {0} into {1}".format(
                    git_project_branch + " " + git_project_origin, project_path), 7065)

        if submodule_failure:
            Log.info(
                "Some Submodule failures have been detected. Backup {0} will not be removed.".format(project_backup_path))
            return False
        if os.path.exists(project_backup_path):
            Log.info("Removing backup...")
            shutil.rmtree(project_backup_path)
        return True
