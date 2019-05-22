import os
from subprocess import PIPE, run, Popen
import sys

# Check if pip3 is installed
command = "pip3 -V"

pipCheck = run(command.split(' '),stdout=PIPE, stderr=PIPE)
stderr = pipCheck.stderr

stderr = stderr.decode('utf-8')

if "not found" in stderr:
	install = os.system("sudo apt install python3-pip")
	if install == 0:
		print("pip3 was successfully installed")
	elif install != 0:
		print("pip3 couldnot be installed")
	

# Check if paramiko module is installed
if 'paramiko' not in sys.modules:

	os.system("sudo pip3 install --upgrade setuptools")
	os.system("sudo apt-get install build-essential libssl-dev \
		libffi-dev python-dev")
	os.system("sudo pip3 install cryptography")

	os.system("sudo pip3 install paramiko")

	if install == 0:
		print("paramiko was successfully installed")
	elif install != 0:
		print("paramiko couldnot be installed")
		
# I was testing for arch linux and saw it has not the nc tool
# Install furthermore nc 
