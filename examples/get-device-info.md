Getting Device Information  
==========================  
Using the `--info` command line argument will gather the following information from a Junos device:  

* Hostname
* Device Model
* Junos Version
* Chassis serial number (or master FPC serial number in an EX VC)

**Single Device**  

	nprintz$ python jaide.py -i 172.25.1.21 --info
	Username: operate
	Password: 
	==================================================
	Results from device: 172.25.1.21

	host-name: Sterling-21-R6 
	IP: 172.25.1.21 
	Model: ex4200-24t 
	Junos: 12.3R3.4 
	Chassis Serial Number (or master FPC in a VC): ***********


**Multiple Devices**  

	nprintz$ python jaide.py -i ~/desktop-link/iplist.txt --info
	Username: operate
	Password: 
	==================================================
	Results from device: 172.25.1.22

	host-name: Cyril-22-R7 
	IP: 172.25.1.22 
	Model: ex4200-24t 
	Junos: 11.4R7.5 
	Chassis Serial Number (or master FPC in a VC): ***********

	==================================================
	Results from device: 172.25.1.21

	host-name: Sterling-21-R6 
	IP: 172.25.1.21 
	Model: ex4200-24t 
	Junos: 12.3R3.4 
	Chassis Serial Number (or master FPC in a VC): ***********

	==================================================
	Results from device: 172.25.1.51

	host-name: EX3300-1-SW1 
	IP: 172.25.1.51 
	Model: ex3300-24p 
	Junos: 11.4R7.5 
	Chassis Serial Number (or master FPC in a VC): ***********

	==================================================
	Results from device: 172.25.1.61

	host-name: OP-SRX220-61 
	IP: 172.25.1.61 
	Model: srx220h-poe 
	Junos: 12.1X45-D20.4 
	Chassis Serial Number (or master FPC in a VC): ***********

