Checking for Interface Errors  
=============================  

## Types of Interfaces  
Currently we check the following logical and physical interface types for errors:  
`ge, fe, ae, xe, so, et, vlan, lo0, and irb`  

## Error Criteria 
The errors we are looking for are in the `Input Errors` and `Output Errors` sections of `show interfaces extensive`. The criteria we use to determine if there are errors is as follows:  

* If there are greater than 50 carrier transitions, we consider that significant. 
* For all other error types, anything above zero is considered significant. 

Fifty carrier transitions may not be that many for your environment (for example, if end users plug in and unplug when they come in and leave each day). Other certain error types may be normal in your environment as well, so you should be aware of what is a good baseline for your network.  

## Single Device  

	$ jaide -i 172.25.1.21 -u root -p root123 errors
	==================================================
	Results from device: 172.25.1.21
	No interface errors were detected on this device.


## Multiple Devices  

	$ jaide -i 192.168.50.95,192.168.50.99 -u root -p root123 errors
	==================================================
	Results from device: 192.168.50.95

	ge-0/0/4 (up/up) has greater than 50 flaps.
	ge-0/0/10 (up/up) has greater than 50 flaps.

	==================================================
	Results from device: 192.168.50.99

	ge-0/0/0 (up/up) has greater than 50 flaps.
	ge-0/0/12 (up/down) has 17 of input-errors.
	ge-0/0/12 (up/down) has 17 of framing-errors.
	ge-0/0/12 (up/down) has greater than 50 flaps.  
