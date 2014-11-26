from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the version number from the relevant file
with open(path.join(here, 'VERSION')) as f:
	version = f.read().strip()

setup (
	name = 'autosubmit',
	version = version,
	description = 'Autosubmit: a versatile tool for managing Global Climate Coupled Models in Supercomputing Environments',
	author = 'Domingo Manubens-Gil',
	author_email = 'domingo.manubens@ic3.cat',
	url = 'https://gitlab.cfu.local/cfu/autosubmit.git',
	download_url = 'https://gitlab.cfu.local/cfu/autosubmit/tarball/autosubmit3.0.0',
	keywords = ['climate', 'workflow', 'HPC'],
	classifiers = [],
	install_requires = ['argparse>=1.2', 'python-dateutil>=1,<2', 'pydot>=1.0.2'],#'matplotlib>=1.1.1', 
	package_dir = {'':'lib'},
	packages = find_packages("lib"),
	scripts = ['bin/expid.py', 'bin/check_exp.py'],
	data_files = [
		('', ['VERSION']),
		('conf', ['lib/autosubmit/config/files/autosubmit.conf','lib/autosubmit/config/files/expdef.conf']),
		('data', ['lib/autosubmit/database/data/autosubmit.sql'])
		]
	#entry_points = {
	#	'console_scripts' : ['check_exp = bin/check_exp.py']
	#	'gui_scripts' : ['monitor = monitor.py']
	#	}
)
