Checking for Interface Errors  
=============================  
Currently we check the following logical and physical interface types for errors:  
`ge, fe, ae, xe, so, et, vlan, lo0, and irb`  

The errors we are looking for are in the `Input Errors` and `Output Errors` sections of a `show interfaces extensive`. The criteria we use to determine if there are errors is as follows. If there are greater than 50 carrier transitions, we consider that significant. For all other error types, anything above zero is considered significant. Fifty carrier transitions may not be that many for your environment (for example, if end users plug in and unplug when they come in and leave each day). Other certain error types may be normal in your environment as well, so you should be aware of what is a good baseline for your network.  

**Single Device**  

	nprintz$ python jaide.py -i 172.25.1.21 -e -u root -p root123
	==================================================
	Results from device: 172.25.1.21
	No interface errors were detected on this device.


**Multiple Devices**  

	nprintz$ python jaide.py -i ~/desktop-link/iplist.txt -e
	Username: root
	Password: 
	==================================================
	Results from device: 172.25.1.22
	No interface errors were detected on this device.

	==================================================
	Results from device: 172.25.1.21
	No interface errors were detected on this device.

	==================================================
	Results from device: 172.25.1.51
	No interface errors were detected on this device.

	==================================================
	Results from device: 172.25.1.61
	ge-0/0/3 has 6090886 of input-l2-channel-errors.
	ge-0/0/4 has 6090885 of input-l2-channel-errors.
