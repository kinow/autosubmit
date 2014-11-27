from os import path
from setuptools import setup
from setuptools import find_packages

here = path.abspath(path.dirname(__file__))

# Get the version number from the relevant file
with open(path.join(here, 'VERSION')) as f:
	version = f.read().strip()

setup (
	name = 'autosubmit',
	license = 'GNU GPL v3',
	platforms = ['GNU/Linux Debian'],
	version = version,
	description = 'Autosubmit: a versatile tool for managing Global Climate Coupled Models in Supercomputing Environments',
	author = 'Domingo Manubens-Gil',
	author_email = 'domingo.manubens@ic3.cat',
	url = 'https://autosubmit.ic3.cat',
	download_url = 'http://ic3.cat/wikicfu/index.php/Tools/Autosubmit',
	keywords = ['climate', 'workflow', 'HPC'],
	install_requires = ['argparse>=1.2', 'python-dateutil>=1,<2', 'pydot>=1.0.2'],#'matplotlib>=1.1.1', 
	packages = find_packages("lib"),
	package_dir = {'':'lib'},
	include_package_data=True,
	package_data = {'autosubmit': [
			'lib/autosubmit/config/files/autosubmit.conf',
			'lib/autosubmit/config/files/expdef.conf',
			'lib/autosubmit/database/data/autosubmit.sql'
		]
		},
	scripts = ['bin/expid.py', 'bin/check_exp.py'],
	#data_files = [
	#	('', ['VERSION']),
	#	('conf', ['lib/autosubmit/config/files/autosubmit.conf','lib/autosubmit/config/files/expdef.conf']),
	#	('data', ['lib/autosubmit/database/data/autosubmit.sql'])
	#	]		
	#entry_points = {
	#	'console_scripts' : ['check_exp = bin/check_exp.py']
	#	'gui_scripts' : ['monitor = monitor.py']
	#	}
)
