Junos Aide (Jaide) and JGUI
===========================
## About  
Contributors: [Geoff Rhodes](mailto:geofflrhodes@gmail.com) and [Nathan Printz](mailto:fragmaster24@gmail.com)  
[Main GitHub](https://github.com/nprintz/jaide)  
[Compiled for OSX](https://github.com/geoffrhodes/jaide-osx-compile)  
[Compiled for Windows](https://github.com/geoffrhodes/jaide-windows-compile)  

## Table of Contents:
* [About](#about)  
* [Description](#description)  
* [Python Requirements](#python-requirements)  
	- [For Command Line Version](#for-command-line-version)  
	- [For GUI Users](#for-gui-users)  
* [Usage](#usage)  
	- [Jaide GUI Users](#jaide-gui-users)  
	- [Jaide.py Command Line Arguments](#jaidepy-command-line-arguments)  
	- [Example Jaide.py Commands](#example-jaidepy-commands)  
	- [Detailed Examples, Tips, and Help](#detailed-examples-tips-and-help)  
	- [Currently Known Limitations](#currently-known-limitations)  
* [Version History](#version-history)  

## Description:
**NOTE** This tool is most beneficial to those who have a basic understanding of JUNOS. This tool can be used to perform several functions against multiple Juniper devices running Junos very easily.  Please understand the ramifications of your actions when using this script before executing it. You can push very significant changes or CPU intensive commands to a lot of devices in the network from one command or GUI execution. This tool should be used with forethought, and we are not responsible for negligence, misuse, time, outages, damages or other repercussions as a result of using this tool. 

This is a python script to augment an engineer's ability to configure and manipulate multiple JUNOS devices at the same time. The command line arguments allow for performing a range of functions. Some features include being able to poll devices for interface errors, grab basic system information, send an operational mode command, or send and commit a file containing a list of set commands. A full list of features and their usage is available in the [Usage](#usage) section below.

There is a GUI that comes along with the script to maintain ease of use for the average network administrator. The GUI has a method to perform every function that the command line can do, all from one easy to use interface. More information on the GUI can be [found below](#jaide-gui-users).

## Python Requirements:

This has been developed on version 2.7 of python. The requirements below are for the non-compiled versions of Jaide and the Jaide GUI. 

#### For Command Line version:
[NCCLIENT](https://github.com/leopoul/ncclient/)  -  https://github.com/leopoul/ncclient/
[PARAMIKO](https://github.com/paramiko/paramiko)  -  https://github.com/paramiko/paramiko  

For using the scp argument, the SCP module is also needed:  
[SCP](https://github.com/jbardin/scp.py)  -  https://github.com/jbardin/scp.py

**Windows** users also require PyCrypto to help with ssh key handling:  
[PyCrypto](http://www.voidspace.org.uk/python/modules.shtml#pycrypto)  -  http://www.voidspace.org.uk/python/modules.shtml#pycrypto

**Linux (Debian/Ubuntu) Note -** We had to get the python-dev package in addition to libxml2-dev and xlst1-dev for NCClient to install, even though they only list the latter two being needed.  

#### For GUI users:
Compiled versions for Mac and Windows come with all pre-reqs packaged in. However, when running jgui.py from the command line, the Jaide GUI requires **all** of the command line prerequisites. In addition, Jaide GUI users on all platforms also require PMW:  
[PMW](http://pmw.sourceforge.net/)  -  http://pmw.sourceforge.net/

**Linux (Debian/Ubuntu)** users of the Jaide GUI will need to get the python-tk package as well.

## Usage: 
#### Jaide GUI Users:
To launch and use the GUI, there are two methods available. Either use the compiled version for your operating system for [Windows](https://github.com/geoffrhodes/jaide-windows-compile) and [Mac](https://github.com/geoffrhodes/jaide-osx-compile). You can also initiate the GUI by navigating to the folder with jgui.py in a terminal window and executing: `python jgui.py`. Further information on the Jaide GUI and operating it can be found in the GUI help file [here](examples/working-with-jgui.md).  

#### Jaide.py Command Line Arguments:
There are many combinations of arguments that can be used to perform all functions available using the Jaide.py command line tool. Two arguments are always required: the `-i` target device(s), and one of the arguments for performing a given function [ -c | -e | --health | --info | -s | --scp | --shell ]. These functions are detailed below in the second table. 

**A destination IP or IP list is required:**  The script will accept a single IP address, a quoted comma separated list, or a file with a list of IPs, separated by newlines. DNS hosts will work as well; resolution uses your machine's specified DNS server(s).  

| Single | Comma Separated List | Filepath |  
| ------ | -------------------- | -------- |  
| `-i ip.add.re.ss` | `-i "ip.add.re.ss1, ip.add.re.ss2, DNS.entry.com"` | `-i /path/to/file/of/ip/addresses.txt` |  

These are the main operations that can be performed. **One and only one of the following is required:**  

| Argument | Description |  
| -------- | ----------- |  
| `-c "quoted operational mode command(s)"` | Send a single operational mode command, a comma separated list of commands, or a filepath to a file containing commands on each line. Can include `show`, `request`, `traceroute`, op scripts, etc. |  
| `-e` | Check all up/up ports for interface errors |  
| `--health` | Pull a health check from the device |  
| `--info` | Retrieve basic device information (Serial, model, etc) |  
| `-s "quoted set command(s)"` | Send a single set command, a quoted comma separated list of commands, or specify a file containing one set command on each line. |  
| `--scp [push OR pull] /source/file/or/folder /destination/file/or/folder` | SCP push or pull operation |  
| `--shell "quoted shell command(s)"` | Similar to -c, except it will run shell commands. |  
 
Authentication arguments are optional on the command line. If they are not provided the script will prompt for them, with the benefit of the password not being echoed to the user.  

| Argument | Description |  
| -------- | ----------- |  
| `-u username` | The username for the device connection(s) |  
| `-p password` | The password for the device connection(s) |  
  
The `-s` argument can take one or none of the three following optional arguments for changing the commit type:  

| Argument | Description |  
| -------- | ----------- |  
| `--confirmed integer_of_minutes` | Will change the commit operation to a commit confirmed for the integer_of_minutes length of time  |  
| `--check` | Instead of committing, this will do a 'commit check' and return the output, letting you know if it passed or not, and why.  | 
| `--blank` | Make a commit with no set commands, a 'commit blank'. Useful for confirming a commit confirmed. |  
  

#### Example jaide.py commands:
Check the target IP for interface errors on all its up/up interfaces, it will prompt for authentication.  
`python jaide.py -i 10.2.10.12 -e`

Backup the primary partition to the backup slice, increasing the timeout value so the NCClient connection doesn't get lost.  
`python jaide.py -i 10.10.10.10 -c 'request system snapshot slice alternate' -t 1800`

Send a list of set commands and commit them to a list of IPs, without being prompted for username/password.  
`python jaide.py -u user -p mypassword -i ~/Downloads/iplist.txt -s ~/Desktop/list_of_set_commands.txt`

SCP push the local code file *~/Downloads/jinstall-ex-2200-12.3R3.4-domestic-signed.tgz* file to an IP list and put it in the */var/tmp* folder.  
`python jaide.py -u user -p mypassword -i ~/Downloads/iplist.txt --scp push ~/Downloads/jinstall-ex-2200-12.3R3.4-domestic-signed.tgz /var/tmp/`

SCP pull the remote */var/tmp* directory on an IP list to the local *~/Desktop/IPaddress_tmp* folders.  
`python jaide.py -u user -p mypassword -i ~/Downloads/iplist.txt --scp pull /var/tmp ~/Desktop/`  

Send a blank commit.  
`python jaide.py -u user -p mypassword -i 10.0.0.123 --blank`  

#### Detailed Examples, Tips, and Help:

* [Some JGUI Tips and Notes](examples/working-with-jgui.md)  
* [Authentication Options - The `-u` and `-p` arguments](examples/working-with-authentication.md)  
* [Checking Interface Errors - The `-e` argument](examples/checking-interface-errors.md)  
* [Getting Device Info - The `-I` argument](examples/get-device-info.md)  
* [Getting Health Checks - The `-H` argument](examples/getting-health-checks.md)  
* [Making Commits - The `-s` argument](examples/making-commits.md)  
* [Modifying Timeout Values](examples/working-with-timeout.md)  
* [Shell and Operational Commands - The `-l` and `-c` arguments](examples/shell-and-operational-commands.md)  
* [Working with Multiple Devices - The `-i` argument](examples/working-with-many-devices.md)  
* [Working with Pipes inside commands](examples/working-with-pipes.md)  
* [Working with SCP - The `-S` argument](examples/scp-files-and-folders.md)  

#### Currently Known Limitations  
* The SCP command is known to break in two scenarios. If it comes across a file that the user credentials used to authenticate doesn't have permissions for, it will stop transferring. The other case is if you are transferring a file to a location where a folder exists by the same name. In both of these cases, the transfer will stop, and anything after that file will not be transferred (if the transfer was recursive). We have posed this to the creators of the SCP module, and are awaiting a new version/feedback.  


## Version History:
* v0.9.1  -  Updated the links in all example files for the github repo. Updated the reamdme with some other documentation and about info. 
* v0.9.0  -  Initial Release. Includes jaide.py script for the command line feature set and jgui.py for the additional GUI wrapper. 
