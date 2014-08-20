Using Shell and Operational Commands
====================================

Jaide and JGUI can be used to send single or multiple commands to a single or multiple Junos devices. Both the `--shell` and `-c` arguments act similarly to `-s` and `-i` in the fact that they can take one of three types of strings. They are a single quoted command, and quoted comma separated list of commands, or a filepath pointing to a file with a list of commands, each on a separate line. We will show these three methods in the following examples.

## Shell Commands

Here we use the shell argument to simply print the working directory when logging in as root. 

	$ python jaide.py -i 172.25.1.21 --shell pwd
	==================================================
	Results from device: 172.25.1.21
	> pwd

	/var/root

Here we use the shell argument to print the working directory, change directories and print again.

	$ python jaide.py -i 172.25.1.21 --shell "pwd,cd /var/tmp, pwd"
	==================================================
	Results from device: 172.25.1.21
	> pwd

	/var/root

	> cd /var/tmp


	> pwd

	/var/tmp

Here we use a file containing the following contents:

	pwd 
	cd /var/tmp
	pwd
	ls -lap
	touch my-new-file
	ls -lap

These are carried out sequentially with session based context:

	$ python jaide.py -i 172.25.1.21 --shell ~/Desktop/shelllist.txt 
	==================================================
	Results from device: 172.25.1.21
	> pwd

	/var/home/operate

	> cd /var/tmp


	> pwd

	/var/tmp

	> ls -lap

	total 220
	drwxrwxrwt   5 root     field   1536 Jul  2 13:27 ./
	drwxr-xr-x  33 root     wheel    512 Jun 13  2013 ../
	-rw-r--r--   1 operate  field      0 Dec 26  2012 .localized
	drwxrwxr-x   2 root     wheel    512 Dec 31  2004 .snap/
	drwxr-xr-x   2 root     field    512 Jun 13  2013 gres-tp/
	drwxr-xr-x   2 root     field    512 Jun 13  2013 rtsdb/

	> touch my-new-file


	> ls -lap

	total 220
	drwxrwxrwt   5 root     field   1536 Jul 10 06:54 ./
	drwxr-xr-x  33 root     wheel    512 Jun 13  2013 ../
	-rw-r--r--   1 operate  field      0 Dec 26  2012 .localized
	drwxrwxr-x   2 root     wheel    512 Dec 31  2004 .snap/
	drwxr-xr-x   2 root     field    512 Jun 13  2013 gres-tp/
	-rw-r--r--   1 operate  field      0 Jul 10 06:54 my-new-file
	drwxr-xr-x   2 root     field    512 Jun 13  2013 rtsdb/


## Operational Commands

Operational commands can be sent to any number of Junos devices using the `-c` argument. Two things of note for this argument are the fact that commands can be abbreviated, and the use of pipes is available. Abbreviating commands is a good way to save typing time, as long as the abbreviations that you are typing are not ambiguous and can only mean one command. Be aware of the model of device you are sending your commands to. For example `sh sy up` on an EX4200 would expand out successfully to `show system uptime`. However on an MX series device, the term `sy` could ambiguously mean `system` or `synchronous-ethernet`, so the command will fail.  

Any command that can be run from operational mode should be valid. This can include `show`, `request`, `ping`, `traceroute`, op scripts, etc. Be aware that just doing `ping 8.8.8.8` will result in output that never normally stops, breaking the script. To use ping, always include the count parameter to ensure output will end: `ping count 10 8.8.8.8` or `ping count 100 rapid www.yahoo.com`. 

Pipes are a very useful tool for filtering or manipulating the output of a command. There is an [entire example document](working-with-pipes.html) on their use for both command line and GUI users named `working-with-pipes.html`. You will also notice that we unconditionally add a `| no-more` to all operational mode commands to ensure output is not buffered.  

For the first example, we use a single command. Note the use of an abbreviated command.  

	$ python jaide.py -i 172.25.1.22 -c "sh cha rout"
	==================================================
	Results from device: 172.25.1.22
	> sh cha rout | no-more

	Routing Engine status:
	  Slot 0:
	    Current state                  Master
	    Temperature                 36 degrees C / 96 degrees F
	    CPU temperature             36 degrees C / 96 degrees F
	    DRAM                      1024 MB
	    Memory utilization          38 percent
	    CPU utilization:
	      User                       2 percent
	      Background                 0 percent
	      Kernel                     1 percent
	      Interrupt                  0 percent
	      Idle                      97 percent
	    Model                          EX4200-24T, 8 POE
	    Serial ID                      ***********
	    Start time                     2014-04-25 19:39:43 UTC
	    Uptime                         25 days, 6 hours, 34 minutes, 30 seconds
	    Last reboot reason             Router rebooted after a normal shutdown.
	    Load averages:                 1 minute   5 minute  15 minute
	                                       0.04       0.03       0.04

The second example shows some use of piping. 

	$ python jaide.py -i 172.25.1.13 -c "sh log | match mess, sh int terse | except ge-"
	==================================================
	Results from device: 172.25.1.13
	> sh log | match mess | no-more

	-rw-rw----   1 root  wheel   261841 Jul  9 22:17 default-log-messages
	-rw-rw----   1 root  wheel   489731 Jul 10 15:42 messages
	-rw-rw----   1 root  wheel    33010 Jul  9 04:15 messages.0.gz
	-rw-rw----   1 root  wheel    33320 Jul  5 21:00 messages.1.gz
	-rw-rw----   1 root  wheel    33917 Jul  2 14:00 messages.2.gz
	-rw-rw----   1 root  wheel    41080 Jun 29 07:00 messages.3.gz
	-rw-rw----   1 root  wheel    33850 Jun 26 05:15 messages.4.gz
	-rw-rw----   1 root  wheel    32991 Jun 23 00:15 messages.5.gz
	-rw-rw----   1 root  wheel    32892 Jun 19 18:45 messages.6.gz
	-rw-rw----   1 root  wheel    33685 Jun 16 12:45 messages.7.gz
	-rw-rw----   1 root  wheel    33347 Jun 13 07:15 messages.8.gz
	-rw-rw----   1 root  wheel    32672 Jun 10 01:30 messages.9.gz

	> sh int terse | except ge- | no-more

	Interface               Admin Link Proto    Local                 Remote
	lc-0/0/0                up    up
	lc-0/0/0.32769          up    up   vpls    
	pfe-0/0/0               up    up
	pfe-0/0/0.16383         up    up   inet    
	                                   inet6   
	pfh-0/0/0               up    up
	pfh-0/0/0.16383         up    up   inet    
	xe-0/0/0                up    down
	xe-0/0/1                up    down
	xe-0/0/2                up    down
	xe-0/0/3                up    down
	gr-0/0/10               up    up
	gr-0/0/10.0             up    down inet     212.212.212.1/24
	                                   inet6    fe80::5e5e:ab00:28d8:bdff/64
	ip-0/0/10               up    up
	lt-0/0/10               up    up
	lt-0/0/10.10            up    up   inet     7.7.7.1/30      
	lt-0/0/10.20            up    up   inet     7.7.7.2/30      
	mt-0/0/10               up    up
	pd-0/0/10               up    up
	pe-0/0/10               up    up
	ut-0/0/10               up    up
	cbp0                    up    up
	demux0                  up    up
	dsc                     up    up

For the final example we use a file of operational commands with the following contents:

	show version
	show interfaces terse | match "ge-0/0/0|lo0"
	show rou 0/0 exa
	show chas rou

The output below is generated from these commands:

	$ python jaide.py -i 172.25.1.22 -c ~/desktop-link/oplist.txt 
	==================================================
	Results from device: 172.25.1.22
	> show version | no-more

	fpc0:
	--------------------------------------------------------------------------
	Hostname: Cyril-22-R7
	Model: ex4200-24t
	JUNOS Base OS boot [11.4R7.5]
	JUNOS Base OS Software Suite [11.4R7.5]
	JUNOS Kernel Software Suite [11.4R7.5]
	JUNOS Crypto Software Suite [11.4R7.5]
	JUNOS Online Documentation [11.4R7.5]
	JUNOS Enterprise Software Suite [11.4R7.5]
	JUNOS Packet Forwarding Engine Enterprise Software Suite [11.4R7.5]
	JUNOS Routing Software Suite [11.4R7.5]
	JUNOS Web Management [11.4R7.5]
	JUNOS FIPS mode utilities [11.4R7.5]


	> show interfaces terse | match "ge-0/0/0|lo0" | no-more

	ge-0/0/0                up    up
	lo0                     up    up
	lo0.0                   up    up   inet     5.5.5.5/24      


	> show rou 0/0 exa | no-more


	inet.0: 21 destinations, 21 routes (21 active, 0 holddown, 0 hidden)
	+ = Active Route, - = Last Active, * = Both

	0.0.0.0/0          *[Static/5] 1w0d 20:56:27
	                    > to 172.25.1.1 via me0.0


	> show chas rou | no-more

	Routing Engine status:
	  Slot 0:
	    Current state                  Master
	    Temperature                 37 degrees C / 98 degrees F
	    CPU temperature             37 degrees C / 98 degrees F
	    DRAM                      1024 MB
	    Memory utilization          39 percent
	    CPU utilization:
	      User                       2 percent
	      Background                 0 percent
	      Kernel                     1 percent
	      Interrupt                  0 percent
	      Idle                      98 percent
	    Model                          EX4200-24T, 8 POE
	    Serial ID                      ***********
	    Start time                     2014-04-25 19:39:43 UTC
	    Uptime                         25 days, 6 hours, 30 minutes, 28 seconds
	    Last reboot reason             Router rebooted after a normal shutdown.
	    Load averages:                 1 minute   5 minute  15 minute
	                                       0.08       0.03       0.05


