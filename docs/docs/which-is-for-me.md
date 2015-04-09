## What are They?  
The Jaide project is split into two packages, the `jaide` package, and the `jaidegui` package.  

Currently, the `jaide` Python package includes two things: the Jaide class library for developers, and a CLI tool for network administrators and engineers.  

The `jaidegui` package is a separate Github repository, for ease of change control and management. It includes the GUI and the compiled versions, and can be found [here](https://github.com/NetworkAutomation/jaidegui).  

## Which is for me?  

 * **Are you wanting to easily manipulate Junos devices using a GUI instead of a CLI, and don't want to worry about Python or programming?**  
 	- We recommend the latest compiled Mac or Windows version of the Jaide GUI available on the [Jaide GUI github page](https://github.com/NetworkAutomation/jaidegui).  

TODO: update links.  

 * **Are you wanting to easily manipulate Junos devices through a CLI tool that can be used on any OS?**  
 	- We recommend following the [pip installation instructions](installation.md) and using the `jaide` command that is installed into your OS PATH variable. Basic command usage can be [found here](usage.md). Further specific examples are in the `CLI Examples` section of the [docs](TODO: READTHEDOCS page).  


 * **Are you wanting to write python scripts that can manipulate Junos?**  
 	- Follow the [pip installation instructions](installation.md) and take a look at the [Jaide Class Examples](examples/lib/examples.md) section of the docs.  

 * **Are you wanting to help work on the Jaide project, or just want to take a look under the hood of the CLI tool or Jaide library?**  
 	- [Download](https://github.com/NetworkAutomation/jaide) the source code, and start poking around!
 