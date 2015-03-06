Junos Aide (Jaide) and the CLI tool
===================================
## About  
Contributors: [Nathan Printz](https://github.com/nprintz) and [Geoff Rhodes](https://github.com/geoffrhodes)  
[Jaide Repo](https://github.com/NetworkAutomation/jaide)  
[Jaide GUI Repo](https://github.com/NetworkAutomation/jaide-gui)  
[Pypi Page](link to pypi package)
[Full documentation on Read The Docs](link to read the docs home page)
[OSX/Windows Compiled Versions](JAIDE GUI latest release page)  

## Table of Contents:
* [About](#about)  
* [Description](#description)  
* [Jaide vs the CLI tool vs the GUI](#jaide-vs-the-cli-tool-vs-the-gui)  
	- [What are They?](#what-are-they)  
	- [Which is for me?](#which-is-for-me)  
* [Installation](#installation)  
* [Python Requirements](#python-requirements)  
* [Usage](#usage)  

## Description:

The `jaide` package contains two parts: a class library for developers (from here on called Jaide), and a CLI tool for network engineers (referred to as the CLI tool). The function of the Jaide class is to allow an engineer or developer to create and use a Jaide object for manipulating Junos devices. Similarly, the CLI tool can be used to manipulate or retrieve information/files/output from one or many devices. Some features of both Jaide and the CLI tool include being able to poll devices for interface errors, grab basic system information, send any operational mode commands, send and commit a file containing a list of set commands, copy files to/from devices, get a configuration diff between two devices, perform a commit check, and run shell commands. A full list of features and their usage is available in the [documentation](READ THE DOCS page).  

Jaide, and therefore the CLI tool and the Jaide GUI, leverage several connection types to JunOS devices using python, including: ncclient, paramiko, and scp. With this base of packages, our goal is the ability to perform as many functions that you can do by directly connecting to a device from a remote, programmatic interface (either Jaide object, or the CLI tool). Since we can perform these functions easily from one remote interface, we can also leverage multiprocessing for manipulating multiple devices simultaneously. Both the CLI tool and the GUI leverage multiprocessing for this purpose.  

**NOTE** This tool is most beneficial to those who have a basic understanding of JUNOS. This tool can be used to perform several functions against multiple Juniper devices running Junos very easily.  Please understand the ramifications of your actions when using this tool before executing it. You can push very significant changes or CPU intensive commands to a lot of devices in the network from one command or GUI execution. This tool should be used with forethought, and we are not responsible for negligence, misuse, time, outages, damages or other repercussions as a result of using this tool.  

## Jaide vs the CLI tool vs the GUI  
#### What are They?  
The Jaide project is split into two packages, the `jaide` package, and the `jaide-gui` package.  

Currently, the `jaide` Python package includes two things: the Jaide class library for developers, and a CLI tool for network administrators and engineers.  

The `jaide-gui` package is a separate Github repository, for ease of change control and management. It includes the GUI and the compiled versions, and can be found [here](https://github.com/NetworkAutomation/jaide-gui).  

#### Which is for me?  

 * **Are you wanting to easily manipulate Junos devices using a GUI instead of a CLI, and don't want to worry about Python or programming?**  
 	- We recommend the latest compiled Mac or Windows version of the Jaide GUI available on the [Jaide GUI github page](https://github.com/NetworkAutomation/jaide-gui).  

TODO: update links.  

 * **Are you wanting to easily manipulate Junos devices through a CLI tool that can be used on any OS?**  
 	- We recommend following the [pip installation instructions](#installation) and using the `jaide` command that is installed into your OS PATH variable. Basic command usage can be [found here](READTHEDOCS basic usage page). Further specific examples are in the CLI examples section of the [docs](READTHEDOCS page).  


 * **Are you wanting to write python scripts that can manipulate Junos?**  
 	- Follow the [pip installation instructions](#installation) and take a look at the [Jaide Class Examples](READTHEDOCS class examples page) section of the docs.  

 * **Are you wanting to help work on the Jaide project, or just want to take a look under the hood of the CLI tool or Jaide library?**  
 	- [Download](https://github.com/NetworkAutomation/jaide) the source code, and start poking around!

## Installation

The easiest way to install Jaide is through pip:  

	> pip install jaide  

Manual installation can be accomplished by downloading the source code and running the following command:  

	> python setup.py install  

## Python Requirements:

Jaide is unfortunately only available on Python version 2.7, due to a required package being Python 2.7 only compatible.

Pip should handle retrieving any necessary requirements, but we list them here for verbosity. The versions of these packages below are the ones that we've tested with.  

[NCCLIENT >=0.4.2](https://github.com/leopoul/ncclient/)  -  https://github.com/leopoul/ncclient/  
[PARAMIKO >=1.14.0](https://github.com/paramiko/paramiko)  -  https://github.com/paramiko/paramiko   
[SCP 0.8.0](https://github.com/jbardin/scp.py)  -  https://github.com/jbardin/scp.py  

The CLI tool has the following additional requirements:  
[COLORAMA 0.3.3](https://pypi.python.org/pypi/colorama) - https://pypi.python.org/pypi/colorama  
TODO: maybe not?  
[CLICK 3.3](http://click.pocoo.org/3/) - http://click.pocoo.org/3/  

## Usage: 
Full [usage](READTHEDOCS basic usage page) documentation and [version history](READTHEDOCS version history page) can be found on the [Read The Docs site](link to READTHEDOCS main page).
