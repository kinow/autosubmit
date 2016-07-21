import os


def generate_experiment_cmd(hpc, description):
    return 'autosubmit expid -H ' + hpc + ' -d ' + description


def create_experiment_cmd(experiment_id):
    return 'autosubmit create ' + experiment_id + ' -np'


def run_experiment_cmd(experiment_id):
    return 'autosubmit run ' + experiment_id


def create_database_cmd():
    return 'autosubmit install'
