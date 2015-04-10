Version History
===============

## v2.0.0  

**Major Restructuring**, including the following:  

* What used to be the `jaide.py` CLI script has now been broken up into several files for modularity and extensibility:  
  * core.py is the base framework, and includes the new Jaide() class that can be imported and used in other python scripts/packages for manipulating Junos devices.  
  * cli.py is the command line interface utility, and is what the user directly interfaces with using the new `jaide` command.  
  * wrap.py is the middle man between core.py and cli.py that provides the error-handling and pretty-printing of output from the Jaide class object that the CLI wants to show to the user.  
* The Jaide GUI has been separated into it's own [package](https://pypi.python.org/pypi/jaide) and [github repo](https://github.com/NetworkAutomation/jaidegui) for ease of tracking GUI specific docs/changes.  
* Jaide is now utilizes setuptools for installing the package into the target python environment.  
  * This allows the Jaide CLI tool to be available system-wide due to setuptools installing the `jaide` command into the OS PATH variable.
* Because Jaide uses setuptools now, it is also available via pip!    
* Two new commands have been added, allowing [comparison of the configuration between two devices](examples/cli/diff-config.md) and [comparing a list of set commands against the running config](examples/cli/show-compare.md).  
* The Jaide CLI tool now uses `click` instead of `argparse`, for a better CLI experience. This has modified how the jaide command is used. Refer to the [documentation](usage.md) for the Jaide CLI tool and the CLI examples documentation.  
* Getting basic device info now also includes system uptime and current time.
* Better Health Check support for EX2200-C and SRX series devices.
* new --quiet option for CLI to suppress all output.
* Better error handling for bad xpath expressions.
* Adding several testing and building scripts in the source code /testing folder to make our development lies easier.  
* Many changes to bring us in line with PEP 8 and PEP 257.  
* Many documentation changes, including using `mkdocs` for easy generation.  
  * All docs are now posted on [Read The Docs](TODO: link to READTHEDOCS page for jaide) as well.  

## v1.1.0  

* Added Commit Comment, Commit Synchronize, and Commit At modifiers for commit options.  
* We have rewritten how templates are saved and loaded to a more streamlined method. This ensures that we can add any number of more options without ordering being an issue. Any old templates *should* still work, but if you have problems, try making a new one and using it before opening an issue.  
* Added defaults to JGUI. A defaults.ini file is a special template that can be used to prepopulate data into the options on program load. You can save the current options as the defaults from the `File` menu.  
* A new argument (-f/--format) is available to print any command with xml output instead of text. This also allows for xml xpath filtering. More information can be found in the Working with XML document. Shoutout to [Jeff Loughridge](https://github.com/jeffbrl) for his driving support on this feature.  
* Writing output to a file in Jaide/JGUI now supports splitting the output on a per device basis. Check the documentation for the -w parameter of Jaide.  
* Added some additional error checking and improved input validation in JGUI.
* Reworked GUI look and feel a little bit for a better experience. 
* Commit Confirmed now works as intended. Fixed the instant rollback bug on Junos version >11.4. Note this requires using the custom version of ncclient shipped with our source (compiled version users don't need to worry). 
* Converted all function comments to use the reST standard.  

## v1.0.0  
* Enveloped the binary files on the release page, updated docs to reflect this change. Rolled over to version 1.0.0.   

## v0.9.1  

* Updated the links in all example files for the github repo. Updated the readme with some other documentation and about info.  

## v0.9.0  

* Initial Release. Includes jaide.py script for the command line feature set and jgui.py for the additional GUI wrapper.  
