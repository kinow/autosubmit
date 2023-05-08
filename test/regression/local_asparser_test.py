"""
This test checks that the autosubmit report command works as expected.
It is a regression test, so it is not run by default.
It only run within my home desktop computer. It is not run in the CI. Eventually it will be included TODO
Just to be sure that the autosubmitconfigparser work as expected if there are changes.
"""

import subprocess
import os
from pathlib import Path
BIN_PATH = '../../bin'

def check_cmd(command, path=BIN_PATH):
    try:
        output = subprocess.check_output(os.path.join(path, command), shell=True, stderr=subprocess.STDOUT)
        error = False
    except subprocess.CalledProcessError as e:
        output = e.output
        error = True
    return output,error

def report_test(expid):
    output = check_cmd("autosubmit report {0} -all -v".format(expid))
    return output
output,error = report_test("a009")
if error:
    print("ERR: autosubmit report command failed")
    print(output.decode("UTF-8"))
    exit(0)
report_file = output.decode("UTF-8").split("list of all parameters has been written on ")[1]
report_file = report_file.split(".txt")[0] + ".txt"
list_of_parameters_to_find = """
DEFAULT.CUSTOM_CONFIG.PRE
DEFAULT.CUSTOM_CONFIG.POST
DIRECTORIES.INDIR
DIRECTORIES.OUTDIR
DIRECTORIES.TESTDIR
TESTKEY
TESTKEY-TWO
TESTKEY-LEVANTE
PLATFORMS.LEVANTE-LOGIN.USER
PLATFORMS.LEVANTE-LOGIN.PROJECT
PLATFORMS.LEVANTE.USER
PLATFORMS.LEVANTE.PROJECT
DIRECTORIES.TEST_FILE
PROJECT.PROJECT_TYPE
PROJECT.PROJECT_DESTINATION
""".split("\n")
expected_output ="""
DIRECTORIES.INDIR=my-updated-indir
DIRECTORIES.OUTDIR=from_main
DIRECTORIES.TEST_FILE=from_main
DIRECTORIES.TESTDIR=another-dir
TESTKEY=abcd
TESTKEY-TWO=HPCARCH is levante
TESTKEY-LEVANTE=L-abcd
PLATFORMS.LEVANTE-LOGIN.USER=b382351
PLATFORMS.LEVANTE-LOGIN.PROJECT=bb1153
PLATFORMS.LEVANTE.USER=b382351
PLATFORMS.LEVANTE.PROJECT=bb1153
PROJECT.PROJECT_TYPE=none
PROJECT.PROJECT_DESTINATION=auto-icon

""".split("\n")
if Path(report_file).exists():
    print("OK: report file exists")
else:
    print("ERR: report file does not exist")
    exit(0)
for line in Path(report_file).read_text().split("\n"):
    if line.split("=")[0] in list_of_parameters_to_find[1:-1]:
        if line in expected_output:
            print("OK: " + line)
        else:
            for error_line in expected_output:
                if line.split("=")[0] in error_line:
                    print(f"ERR: {line.split('=')[0]} loaded value is {line.split('=')[1]} EXPECTED: " + error_line)
                    break

