import os
from setuptools import setup, find_packages

def read(fname):
	return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(	
	name = "iotronic",
	#packages = ["cwProbe", "plugins"],
	packages = find_packages(),
	version = "0.1",
	description = "iot",
	author = "",
	author_email = "",
	url = "",
	download_url = "",
	keywords = ["iotronic", "iot", "s4t"],
	classifiers = [
	        "Programming Language :: Python",
	        "Programming Language :: Python :: 2.7",
	        "Development Status :: 4 - Beta",
	        "Environment :: Other Environment",
	        "Intended Audience :: Developers",
	        "License :: OSI Approved :: GNU General Public License (GPL)",
	        "Operating System :: OS Independent",
	        "Topic :: Software Development :: Libraries :: Python Modules",
	],
	license='GPL',
	platforms=['Any'],
	#provides=['plugins',],
	

	dependency_links = [
	
	],


	
	entry_points={
    	#'cwprobe.plugins.monitors': [
    	    #'mycheck = plugins.cwpl_mycheckpoint:Cwpl_MyCheckPoint',
    	    #'cpu = plugins.cwpl_cpu:Cwpl_Cpu',
			#'awstats = plugins.cwpl_awstats:Cwpl_Awstat',
    	    #'test = plugins.cwpl_test:Cwpl_Test',
    	#],
	},
	
    install_requires=[
		#'setuptools',
		#'greenlet',
		#'httplib2',
		#'stevedore',
		#'psutil',
		#'qpid-python==0.20',
		#'pyyamllib',
		#'pyloglib',
		#'cwconfparser',
		#'MySQL-python',
    ],
	

	include_package_data = True,
	
	data_files=[
		('/usr/bin', ['bin/iotronic-conductor']),
		('/usr/bin', ['bin/iotronic']),
    ],
    
	
    #package_data = {
    #    '': ['scripts/etc/init.d/cwProbe', 'scripts/usr/bin/cwProbe'],
    #},
	
	
	#options = {'bdist_rpm':{'post_install' : 'scripts/post_install'},
	
	zip_safe=False,
	#long_description=read('README.txt')


)
