from autosubmit.config.config_common import AutosubmitConfig
from autosubmit.config.parser_factory import ConfigParserFactory
from autosubmit.config.log import Log
from tests_utils import check_cmd, next_experiment_id, copy_experiment_conf_files, create_database, clean_database
from tests_commands import *
from threading import Thread
from time import sleep

# Configuration file where the regression tests are defined with INI style
tests_parser_file = 'tests.conf'

# Path where the temporal files (db, experiments, etc) fill be saved
db_path = './db'

# Initial experiment id
initial_experiment_id = 'a000'


def run_test_case(experiment_id, name, hpc_arch, description, src_path):
    if not check_cmd(generate_experiment_cmd(hpc_arch, description)):
        Log.critical('Error while generating the experiment {0}({1})', name, experiment_id)
        return False

    copy_experiment_conf_files(db_path, src_path, experiment_id)

    sleep(5)  # Avoiding synchronization problems while copying

    if not check_cmd(create_experiment_cmd(experiment_id)):
        Log.critical('Error while creating the experiment {0}({1})', name, experiment_id)
        return False

    if not check_cmd(run_experiment_cmd(experiment_id)):
        Log.critical('Error while running the experiment {0}({1})', name, experiment_id)
        return False

    # Everything was OK
    Log.result('Test {0}({1}) passed successfully', name, experiment_id)


def run(current_experiment_id):
    # Local variables for testing
    test_threads = []
    tests_parser = AutosubmitConfig.get_parser(ConfigParserFactory(), tests_parser_file)

    # Resetting the database
    clean_database(db_path)
    create_database()

    # Main loop to run all the tests
    for section in tests_parser.sections():
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


if __name__ == "__main__":
    run(initial_experiment_id)
