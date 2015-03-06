Version History
===============

## Roadmap  
TODO: update roadmap.  
These are features we'd like to implement, but will likely take some additional time, or coordinating with other package writers to implement.  

* Commit Confirmed fix
	-	We have made a pull request on the ncclient repo to fix the commit confirmed functionality of the juniper RPC method in ncclient. The reason for this is we had found a bug in v1.0 of Jaide whereby commit confirmed operations would successfully commit initially, but would be immediately rolled back. We traced the problem to ncclient, and Junos itself. Turns out that Junos changed at some point between 11.4 and 12.3, modifying the expected XML RPC for a commit operation, and this broke commit confirms on ncclient. We have made a pull request to fix this against ncclient. In the meantime until they accept and pull in the change, we felt we should include a fixed version of ncclient directly in our project so that people can use the other additional features from Jaide v1.1.0 sooner rather than later, and with working commit confirmed.  

## v2.0.0  

**Major Restructuring**, including the following:  

* A new object class, Jaide() is available for extending Jaide into other scripts
* The Jaide GUI has been separated into it's own [package](link to pypi package) and [github repo](https://github.com/NetworkAutomation/jaide-gui) for ease of tracking GUI specific docs/changes.  
* Jaide is now available via pip. Along with this, the Jaide CLI tool is globally available due to setuptools installing the `jaide` command into the OS PATH variable.  
* A new core feature has been [added](link to diff_config docs), allowing comparison of the configuration between two devices.  
* The Jaide CLI tool uses the Jaide class, for better code modularity.
* The Jaide CLI tool now uses `click` instead of `argparse`, for a better CLI experience. This has modified how the jaide command is used. Refer to the [documentation](usage.md) for the Jaide CLI tool.  
* Better error handling for bad xpath expressions.
* Added testing scripts to the /testing directory of the source code.  
* Many changes to bring us in line with PEP 8 and PEP 257 (more comment changes to come to allow for read the docs support).  
* Many documentation changes, including using `mkdocs` with `autodocs` for easy generation. All docs are now posted on [Read The Docs](link to READTHEDOCS page for jaide) as well.  

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
