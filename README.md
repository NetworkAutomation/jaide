Junos Aide (Jaide) and JGUI
===========================
## About  
Contributors: [Geoff Rhodes](https://github.com/geoffrhodes) and [Nathan Printz](https://github.com/nprintz)  
[Source Repo](https://github.com/NetworkAutomation/jaide)  
[OSX/Windows Compiled Versions](https://github.com/NetworkAutomation/jaide/releases/latest)  

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
	- [Roadmap](#roadmap)  
* [Version History](#version-history)  

## Description:
Jaide contains two parts: a python script and GUI that allows an engineer to do everything the script does. The function of Jaide is to augment an engineer's ability to configure and manipulate multiple JunOS devices at the same time. The command line arguments allow for performing a range of functions. Some features include being able to poll devices for interface errors, grab basic system information, send any operational mode commands, or send and commit a file containing a list of set commands. A full list of features and their usage is available in the [Usage](#usage) section below.

The GUI that comes along with the script maintains ease-of-use for the average network administrator. The GUI has a method to perform every function that the command line can do, all from one easy to use interface. More information on the GUI can be [found below](#jaide-gui-users).

Jaide and the JGUI leverage netconf connections to JunOS devices using python and the python modules: ncclient, paramiko, and scp. With this base of modules, our goal is the ability to perform as many functions that you can do by directly connecting to a device from our remote interface. Since we can do these remotely from this interface, you can also therefore perform these functions rapidly against multiple devices very easily. Pushing code and upgrading 20 devices within a network is a simple task with the Jaide tool in hand. 

**NOTE** This tool is most beneficial to those who have a basic understanding of JUNOS. This tool can be used to perform several functions against multiple Juniper devices running Junos very easily.  Please understand the ramifications of your actions when using this script before executing it. You can push very significant changes or CPU intensive commands to a lot of devices in the network from one command or GUI execution. This tool should be used with forethought, and we are not responsible for negligence, misuse, time, outages, damages or other repercussions as a result of using this tool.  

## Python Requirements:

This has been developed on version 2.7 of python. The requirements below are for the non-compiled versions of Jaide and the Jaide GUI. 

#### For Command Line version:
The versions of these modules below are the ones that we've tested with. 
[NCCLIENT (custom version included)](https://github.com/leopoul/ncclient/)  -  https://github.com/leopoul/ncclient/  
[PARAMIKO 1.14.0](https://github.com/paramiko/paramiko)  -  https://github.com/paramiko/paramiko  

For using the scp argument, the SCP module is also needed:  
[SCP 0.8.0](https://github.com/jbardin/scp.py)  -  https://github.com/jbardin/scp.py

**Windows** users also require PyCrypto to help with ssh key handling:  
[PyCrypto (included with ncclient)](http://www.voidspace.org.uk/python/modules.shtml#pycrypto)  -  http://www.voidspace.org.uk/python/modules.shtml#pycrypto

**Linux (Debian/Ubuntu) Note -** We had to get the python-dev package in addition to libxml2-dev and xlst1-dev for NCClient to install, even though they only list the latter two being needed.  

#### For GUI users:
Compiled versions for Mac and Windows come with all pre-reqs packaged in. However, when running jgui.py from the command line, the Jaide GUI requires **all** of the command line prerequisites. In addition, Jaide GUI users on all platforms also require PMW:  
[PMW 1.3.3](http://pmw.sourceforge.net/)  -  http://pmw.sourceforge.net/

**Linux (Debian/Ubuntu)** users of the Jaide GUI will need to get the `python-tk` package as well.

## Usage: 
#### Jaide GUI Users:
To launch and use the GUI, there are two methods available. The first is to use the compiled version for your operating system for either [Windows or Mac](https://github.com/NetworkAutomation/jaide/releases/latest). The second is initiating the GUI by navigating to the source folder with jgui.py in terminal and executing: `python jgui.py`. Further information on the Jaide GUI and operating it can be found in the GUI help file [here](examples/working-with-jgui.md).  

#### Jaide.py Command Line Arguments:
There are many combinations of arguments that can be used to perform all functions available using the Jaide.py command line tool. Two arguments are always required: the `-i` target device(s), and one of the arguments for performing a given function [ -b | -c | -e | --health | --info | -s | --scp | --shell ]. These functions are detailed below in the second table. 

**A destination IP or IP list is required:**  The script will accept a single IP address, a quoted comma separated list, or a file with a list of IPs, separated by newlines. DNS hosts will work as well; resolution uses your machine's specified DNS server(s).  

| Single | Comma Separated List | Filepath |  
| ------ | -------------------- | -------- |  
| `-i/--ip ip.add.re.ss` | `-i/--ip "ip.add.re.ss1, ip.add.re.ss2, DNS.entry.com"` | `-i/--ip /path/to/file/of/ip/addresses.txt` |  

These are the main operations that can be performed. **One and only one of the following is required:**  

| Argument | Description |  
| -------- | ----------- |  
| `-c/--command "quoted operational mode command(s)"` | Send a single operational mode command, a comma separated list of commands, or a filepath to a file containing commands on each line. Can include `show`, `request`, `traceroute`, op scripts, etc. |  
| `-e/--errors` | Check all up/up ports for interface errors |  
| `-H/--health` | Pull a health check from the device |  
| `-I/--info` | Retrieve basic device information (Serial, model, etc) |  
| `-s/--set "quoted set command(s)"` | Send a single set command, a quoted comma separated list of commands, or specify a file containing one set command on each line. |  
| `-b/--blank` | Make a commit with no set commands, a 'commit blank'. Useful for confirming a commit confirmed. |  
| `-S/--scp [push OR pull] /source/file/or/folder /destination/file/or/folder` | SCP push or pull operation |  
| `-l/--shell "quoted shell command(s)"` | Similar to `-c`, except it will run shell commands. |  
 
Authentication arguments are optional on the command line. If they are not provided the script will prompt for them, with the benefit of the password not being echoed to the user.  

| Argument | Description |  
| -------- | ----------- |  
| `-u/--username USERNAME` | The username for the device connection(s) |  
| `-p/--password PASSWORD` | The password for the device connection(s) |  
  
The `-s` argument can take one or none of the three following optional arguments for changing the commit type:  

| Argument | Description |  
| -------- | ----------- |  
| `-m/--confirm INTEGER_OF_MINUTES` | Will change the commit operation to a commit confirmed for the integer_of_minutes length of time  |  
| `-k/--check` | Instead of committing, this will do a 'commit check' and return the output, letting you know if it passed or not, and why.  | 
  
Other optional arguments:  

| Argument | Description |  
| -------- | ----------- |  
| `-f/--format [text OR xml]` | This changes the output of the command returned from the device. It defaults to 'text', and will only take effect on operational mode commands. With or without -f, you can do xpath filtering, by putting ` % XPATH_EXPRESSION` after your operational command. For example: `show route % //rt-entry`. |  
| `-q/--quiet` | Used in conjunction with `-S/--scp`, when copying to/from a single device, to prevent seeing the callback status of the transfer as it happens. |  
| `-t/--timeout INTEGER_OF_SECONDS` | Will change the timeout for operation sent to the device. Defaults to 300 seconds. Check the help file for timeout. |  
| `-w/--write s/single_OR_m/multiple OUTPUT_FILENAME` | Write the output of the script to a file(s). `-w s ~/Desktop/output.txt` will write all output to one file, whereas `-w multiple ~/Desktop/output.txt` will write one file for each device connecting to, resulting in `~/Desktop/IP_OF_DEVICE_output.txt` being written for each device. |  

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
* [Working with XML - The `-f` argument](examples/working-with-xml.md)  

#### Currently Known Limitations  
* The SCP command is known to break in two scenarios. If it comes across a file that the user credentials used to authenticate doesn't have permissions for, it will stop transferring. The other case is if you are transferring a file to a location where a folder exists by the same name. In both of these cases, the transfer will stop, and anything after that file will not be transferred (if the transfer was recursive). We have posed this to the creators of the SCP module, and are awaiting a new version/feedback.  

#### Roadmap  
These are features we'd like to implement, but will likely take some additional time, or coordinating with other module writers to implement.  

* Commit Confirmed fix
	-	We have made a pull request on the ncclient repo to fix the commit confirmed functionality of the juniper RPC method in ncclient. The reason for this is we had found a bug in v1.0 of Jaide whereby commit confirmed operations would successfully commit initially, but would be immediately rolled back. We traced the problem to ncclient, and Junos itself. Turns out that Junos changed at some point between 11.4 and 12.3, modifying the expected XML RPC for a commit operation, and this broke commit confirms on ncclient. We have made a pull request to fix this against ncclient. In the meantime until they accept and pull in the change, we felt we should include a fixed version of ncclient directly in our project so that people can use the other additional features from Jaide v1.1.0 sooner rather than later, and with working commit confirmed.  

## Version History:
* v1.1.0
	-	Added Commit Comment, Commit Synchronize, and Commit At modifiers for commit options.  
	-	We have rewritten how templates are saved and loaded to a more streamlined method. This ensures that we can add any number of more options without ordering being an issue. Any old templates *should* still work, but if you have problems, try making a new one and using it before opening an issue.  
	-	Added defaults to JGUI. A defaults.ini file is a special template that can be used to prepopulate data into the options on program load. You can save the current options as the defaults from the `File` menu.  
	-	A new argument (-f/--format) is available to print any command with xml output instead of text. This also allows for xml xpath filtering. More information can be found in the Working with XML document. Shoutout to [Jeff Loughridge](https://github.com/jeffbrl) for his driving support on this feature.  
	-	Writing output to a file in Jaide/JGUI now supports splitting the output on a per device basis. Check the documentation for the -w parameter of Jaide.  
	-	Added some additional error checking and improved input validation in JGUI.
	-	Reworked GUI look and feel a little bit for a better experience. 
	-	Commit Confirmed now works as intended. Fixed the instant rollback bug on Junos version >11.4. Note this requires using the custom version of ncclient shipped with our source (compiled version users don't need to worry). 
	-	Converted all function comments to use the reST standard.  
* v1.0.0  -  Enveloped the binary files on the release page, updated docs to reflect this change. Rolled over to version 1.0.0. 
* v0.9.1  -  Updated the links in all example files for the github repo. Updated the readme with some other documentation and about info. 
* v0.9.0  -  Initial Release. Includes jaide.py script for the command line feature set and jgui.py for the additional GUI wrapper. 
