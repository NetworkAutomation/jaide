Working With Authentication
===========================

With the jaide.py command line tool, authentication input is flexible. The authentication can be put directly into the command, if you are okay with typing the password in clear text or no one is watching over your shoulder:  

	python jaide.py -i ~/desktop-link/iplist.txt -hc -u root -p root123  

You can also omit either username and/or password from the command, and the script will ask you for the information accordingly. Note that this can be useful for if people are watching, or you don't want your password in your command history, since the password prompt will not be echoed back to the user.  

	$ python jaide.py -i 172.25.1.21 -info
	Username: operate
	Password: 
	==================================================
	Results from device: 172.25.1.21

	host-name: R6 
	IP: 172.25.1.21 
	Model: ex4200-24t 
	Junos: 12.3R3.4 
	Chassis Serial Number (or master FPC in a VC): *********

Another example only omitting the password:  

	$ python jaide.py -i 172.25.1.21 -info -u root  
	Password: 
	==================================================
	Results from device: 172.25.1.21

	host-name: R6
	IP: 172.25.1.21 
	Model: ex4200-24t 
	Junos: 12.3R3.4 
	Chassis Serial Number (or master FPC in a VC): *********

## For JGUI  

When working with the jgui.py GUI interface for Jaide, the username and password must always be entered into the text entry items. The password will not be readable or able to be copied, as one would expect. 