from autosubmit.config.config_common import AutosubmitConfig
from autosubmit.config.parser_factory import ConfigParserFactory
from autosubmit.config.log import Log
from tests_utils import check_cmd, next_experiment_id, copy_experiment_conf_files, create_database, clean_database
from tests_commands import *
from threading import Thread
from time import sleep
import argparse

# Configuration file where the regression tests are defined with INI style
tests_parser_file = 'tests.conf'

# Path where the temporal files (db, experiments, etc) fill be saved
db_path = './db'

# Initial experiment id
initial_experiment_id = 'a000'


def run_test_case(experiment_id, name, hpc_arch, description, src_path):
    if not check_cmd(generate_experiment_cmd(hpc_arch, description)):
        Log.error('Error while generating the experiment {0}({1})', name, experiment_id)
        return False

    copy_experiment_conf_files(db_path, src_path, experiment_id)

    sleep(5)  # Avoiding synchronization problems while copying

    if not check_cmd(create_experiment_cmd(experiment_id)):
        Log.error('Error while creating the experiment {0}({1})', name, experiment_id)
        return False

    if not check_cmd(run_experiment_cmd(experiment_id)):
        Log.error('Error while running the experiment {0}({1})', name, experiment_id)
        return False

    # Everything was OK
    Log.result('[OK] Test {0}({1}) has been passed successfully', name, experiment_id)


def run(current_experiment_id, only_list=None, exclude_list=None):
    # Local variables for testing
    test_threads = []
    tests_parser = AutosubmitConfig.get_parser(ConfigParserFactory(), tests_parser_file)

    # Resetting the database
    clean_database(db_path)
    create_database()

    # Main loop to run all the tests
    for section in tests_parser.sections():
        # Skipping filtered experiments
        if only_list is not None and section not in only_list:
            Log.warning('Test {0} has been skipped', section)
            continue

        if exclude_list is not None and section in exclude_list:
            Log.warning('Test {0} has been skipped', section)
            continue

        # Getting test settings
        description, hpc_arch, src_path = get_test_settings(section, tests_parser)

        # Running the test as a new thread
        test_threads.append(create_test_thread(current_experiment_id, section, description, hpc_arch, src_path))

        # Updating current experiment id
        current_experiment_id = next_experiment_id(current_experiment_id)

        # Avoiding synchronization problems
        sleep(3)

    # Loop to wait the end of all the running tests
    for test_thread in test_threads:
        test_thread.join()


def create_test_thread(current_experiment_id, name, description, hpc_arch, src_path):
    thr = Thread(target=run_test_case, args=(current_experiment_id, name, hpc_arch, description, src_path), kwargs={})
    thr.start()
    return thr


def get_test_settings(section, tests_parser):
    hpc_arch = tests_parser.get(section, 'HPCARCH')
    description = tests_parser.get(section, 'DESCRIPTION')
    src_path = tests_parser.get(section, 'SRC_PATH')
    return description, hpc_arch, src_path


def create_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", type=str,
                        help="List of experiments to be run, test names separated by white spaces")
    parser.add_argument("--exclude", type=str,
                        help="List of experiments to be avoided, test names separated by white spaces")
    return parser


if __name__ == "__main__":
    args_parser = create_args_parser()

    only = None if args_parser.parse_args().only is None else args_parser.parse_args().only.split()
    exclude = None if args_parser.parse_args().exclude is None else args_parser.parse_args().exclude.split()

    run(initial_experiment_id, only, exclude)
