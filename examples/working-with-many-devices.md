Working With Multiple Devices
=============================

There are three methods for specifying device(s) for jaide.py to communicate with. They all use the `-i` argument.  In any instance where more than one IP is specified, Jaide will read these in and multiprocess against all IPs simultaneously using a multiprocessing pool running (2 * # of CPU cores) instances at a time. A valid DNS resolvable hostname will work in addition to an IP address. The three methods are as follows:

#### A single IP address

A single IP address can be specified:

	$ python jaide.py -i 172.25.1.21 --health

#### Multiple devices using a list

Multiple IP addresses can be passed using a command separated list directly to the `-i` argument with or without spaces. Always be aware of your operating system environment, and the need to quote any argument with spaces. The following was taken from Mac OS X:  

	$ python jaide.py -i 172.25.1.21,172.25.1.22,172.25.1.23 --health  

	$ python jaide.py -i "172.25.1.21, 172.25.1.22, 172.25.1.23" --health  

#### Multiple devices using an IP list file 

If you have a large number of IP addresses that you want to run against, the best method is going to be using an IP list file. The file should be plain text with a single IP address on each line of the file. These will be read and run against simultaneously using a multiprocessing pool.  

	$ python jaide.py -i ~/Desktop/iplist.txt --health

Contents of ~/Desktop/iplist.txt:
	
	172.25.1.51
	172.25.1.61
	172.25.1.22
	172.25.1.21

## For JGUI  

The IP entry field acts as a direct mapping to the `-i` argument for jaide.py. This means that any of the above methods for specifying devices with jaide.py will also work in JGUI. The only difference is that a comma separated list doesn't need to be quoted in JGUI. 
