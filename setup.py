from setuptools import setup, find_packages

with open('VERSION') as file:
	version = file.readline().split('\n')[0]

config = {
	'name' : 'autosubmit',
	'packages' : find_packages(),
	'version' : version,
	'description' : 'Autosubmit: a versatile tool for managing Global Climate Coupled Models in Supercomputing Environments',
	'author' : 'Domingo Manubens-Gil',
	'author_email' : 'domingo.manubens@ic3.cat',
	'url' : 'https://gitlab.cfu.local/cfu/autosubmit.git', # use the URL to the github repo
	'download_url' : 'https://gitlab.cfu.local/cfu/autosubmit/tarball/autosubmit3.0.0', # I'll explain this in a second
	'keywords' : ['climate', 'workflow', 'HPC'], # arbitrary keywords
	'classifiers' : []
}

setup(**config)
