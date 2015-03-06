About Us
========

We are Nathan Printz and Geoff Rhodes.  

Initially, we were working on a project that required us to upgrade the code on several hundred devices. Rather than doing this process manually, we wanted a method for doing this easily from our desk, with one command.  

So we started building a simple script to do just that. In our research for writing this script, we came across existing [Python](https://www.python.org/) packages like [ncclient](https://github.com/leopoul/ncclient/), [paramiko](https://github.com/paramiko/paramiko), and [scp](https://github.com/jbardin/scp.py). Using these, we were able to immediately satisfy the need we had.

However, we thought we could expand on this idea, and do several things. First, if we could create a class for handling the ncclient/paramiko/scp connection to the device, we could have an extensible interface for performing any number of complex operations to a Junos device. Second, by leveraging this class, we could create a better CLI tool for manipulating multiple Junos devices simultaneously. Lastly, we could create a GUI interface and compile it for Mac and Windows. This makes Jaide an easily accessible and intuitive tool for any Network Engineer or Administrator, who simply wants a quicker way to incorporate changes or retrieve information from their network.  
