Getting Device Information  
==========================  
Using the `info` command will gather the following information from a Junos device:  

* Hostname
* Device Model
* Junos Version
* Chassis serial number (or master FPC serial number in an EX VC)
* System Uptime
* Current time according to the device.

## Single Device    

	$ jaide -i 192.168.50.95 info
	Username: operate
	Password: 
	==================================================
	Results from device: 192.168.50.95

	Hostname: Bender
	Model: ex2200-c-12p-2g
	Junos Version: 12.3R3.4
	Routing Engine 0 Serial #: ***********
	Current Time: 2015-03-17 23:52:58 CDT
	Uptime: 207 days,  5:43


## Multiple Devices  

	$ jaide -i ~/desktop-link/iplist.txt info
	Username: operate
	Password: 
	==================================================
	Results from device: 172.25.1.22

	host-name: Cyril-22-R7 
	IP: 172.25.1.22 
	Model: ex4200-24t 
	Junos: 11.4R7.5 
	Chassis Serial Number (or master FPC in a VC): ***********
	Current Time: 2015-03-17 23:52:58 CDT
	Uptime: 192 days,  3:02

	==================================================
	Results from device: 172.25.1.21

	host-name: Sterling-21-R6 
	IP: 172.25.1.21 
	Model: ex4200-24t 
	Junos: 12.3R3.4 
	Chassis Serial Number (or master FPC in a VC): ***********
	Current Time: 2015-03-17 23:52:58 CDT
	Uptime: 181 days,  5:55
