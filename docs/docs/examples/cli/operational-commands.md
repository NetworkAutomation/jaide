Operational Commands
====================

Jaide can be used to send a single or multiple commands to a single or multiple Junos devices. There are several options for how to specify commands. These methods are shared amongst operational commands, shell commands, set commands (for committing), and IP lists for multipel devices. They are a single quoted command, and quoted comma separated list of commands, or a filepath pointing to a file with a list of commands, each on a separate line. We will show these three methods in the following examples.

# Basic Usage

Operational commands can be sent to any number of Junos devices using the `operational` command line argument. Several notes include: commands can be abbreviated, the use of pipes is available, and output can be xpath filtered. Abbreviating commands is a good way to save typing time, as long as the abbreviations that you are typing are not ambiguous and can only mean one command. Be aware of the model of device you are sending your commands to. For example `sh sy up` on an EX4200 would expand out successfully to `show system uptime`. However on an MX series device, the term `sy` could ambiguously mean `system` or `synchronous-ethernet`, so the command will fail.  

Any command that can be run from operational mode should be valid. This can include `show`, `request`, `ping`, `traceroute`, op scripts, etc. Be aware that just doing `ping 8.8.8.8` will result in output that never normally stops, breaking the script. To use ping, always include the count parameter to ensure output will end: `ping count 10 8.8.8.8` or `ping count 100 rapid www.yahoo.com`.  

Pipes are a very useful tool for filtering or manipulating the output of a command. There is an [entire document](http://www.juniper.net/techpubs/en_US/junos14.2/topics/concept/junos-cli-pipe-filter-functions-overview.html) on their use in the Juniper support docs, but we supply more information on using them (and xpath filtering) with jaide below.  

*Note* We unconditionally add a ` | no-more` to all operational mode commands to ensure output is not buffered.  

#### Basic Example 1  
For the first example, we use a single command. Note the use of an abbreviated command.  

	$ jaide -i 172.25.1.22 -u root -p root123 operational "sh cha rout"
	==================================================
	Results from device: 172.25.1.22
	> sh cha rout

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

#### Basic Example 2  
The second example shows some use of piping, and a comma separated list of commands. 

	$ jaide -i 172.25.1.13 -u root -p root123 oper "sh log | match mess, sh int terse | except ge-"
	==================================================
	Results from device: 172.25.1.13
	> sh log | match mess

	-rw-rw----   1 root  wheel   261841 Jul  9 22:17 default-log-messages
	-rw-rw----   1 root  wheel   489731 Jul 10 15:42 messages
	-rw-rw----   1 root  wheel    33010 Jul  9 04:15 messages.0.gz
	-rw-rw----   1 root  wheel    33320 Jul  5 21:00 messages.1.gz
	-rw-rw----   1 root  wheel    33917 Jul  2 14:00 messages.2.gz
	-rw-rw----   1 root  wheel    41080 Jun 29 07:00 messages.3.gz
	-rw-rw----   1 root  wheel    33850 Jun 26 05:15 messages.4.gz
	-rw-rw----   1 root  wheel    32991 Jun 23 00:15 messages.5.gz
	-rw-rw----   1 root  wheel    32892 Jun 19 18:45 messages.6.gz

	> sh int terse | except ge-

	Interface               Admin Link Proto    Local                 Remote
	lc-0/0/0                up    up
	lc-0/0/0.32769          up    up   vpls    
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


#### Basic Example 3 - from a file
For another example we use a file of operational commands with the following contents (commented and empty lines are ignored by jaide):

	# basic commands
	show version
	show route 0/0 exact

	# pipe in command
	show interfaces terse | match "ge-0/0/0|lo0"
	
	# partial commands will be expanded as normal by Junos
	show chas rou

The output below is generated from these commands:

	$ jaide -i 172.25.1.22 -u root -p root123 operational ~/desktop-link/oplist.txt 
	==================================================
	Results from device: 172.25.1.22
	> show version

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


	> show route 0/0 exact


	inet.0: 21 destinations, 21 routes (21 active, 0 holddown, 0 hidden)
	+ = Active Route, - = Last Active, * = Both

	0.0.0.0/0          *[Static/5] 1w0d 20:56:27
	                    > to 172.25.1.1 via me0.0

	> show interfaces terse | match "ge-0/0/0|lo0"

	ge-0/0/0                up    up
	lo0                     up    up
	lo0.0                   up    up   inet     5.5.5.5/24      


	> show chas rou

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



# Working with XML and XPATH

The `-f` or `--format` option can be used to retrieve XML output from the device instead of text output. This can be useful for many reasons, including writing SLAX scripts. 

With or without `-f xml`, you can include a xpath expression to filter the returned XML output. Simply append `% xpath_expression` to the end of an operational command to filter the output and force an XML response. For example: `show version % //package-information` returns all the `<package-information>` nodes in the XML response to `show version | display xml`. This is shown below in the second example where alternating commands with and without xpath filters are sent, and only the ones with xpath expressions are returned in XML output, the rest are text.

#### XML Example 1

Here we simply change the output format of the `show version` command to be xml. Note `-f xml` will force all commands to be returned as XML, if more than one is sent.  

	$ jaide -i 172.25.1.21 -u root -p root123 operational "show version" -f xml
	==================================================
	Results from device: 172.25.1.21
	> show version | display xml

	<rpc-reply xmlns:junos="http://xml.juniper.net/junos/12.3R3/junos">
	    <multi-routing-engine-results>
	        
	        <multi-routing-engine-item>
	            
	            <re-name>fpc0</re-name>
	            
	            <software-information>
	                <host-name>Sterling-21-R6</host-name>
	                <product-model>ex4200-24t</product-model>
	                <product-name>ex4200-24t</product-name>
	                <package-information>
	                    <name>junos</name>
	                    <comment>JUNOS Base OS boot [12.3R3.4]</comment>
	                </package-information>
	                <package-information>
	                    <name>jbase</name>
	                    <comment>JUNOS Base OS Software Suite [12.3R3.4]</comment>
	                </package-information>
	                <package-information>
	                    <name>jkernel-ex</name>
	                    <comment>JUNOS Kernel Software Suite [12.3R3.4]</comment>
	                </package-information>
	                <package-information>
	                    <name>jcrypto-ex</name>
	                    <comment>JUNOS Crypto Software Suite [12.3R3.4]</comment>
	                </package-information>
	                <package-information>
	                    <name>jdocs-ex</name>
	                    <comment>JUNOS Online Documentation [12.3R3.4]</comment>
	                </package-information>
	                <package-information>
	                    <name>jswitch-ex</name>
	                    <comment>JUNOS Enterprise Software Suite [12.3R3.4]</comment>
	                </package-information>
	                <package-information>
	                    <name>jpfe-ex42x</name>
	                    <comment>JUNOS Packet Forwarding Engine Enterprise Software Suite [12.3R3.4]</comment>
	                </package-information>
	                <package-information>
	                    <name>jroute-ex</name>
	                    <comment>JUNOS Routing Software Suite [12.3R3.4]</comment>
	                </package-information>
	                <package-information>
	                    <name>jweb-ex</name>
	                    <comment>JUNOS Web Management [12.3R3.4]</comment>
	                </package-information>
	                <package-information>
	                    <name>fips-mode-powerpc</name>
	                    <comment>JUNOS FIPS mode utilities [12.3R3.4]</comment>
	                </package-information>
	            </software-information>
	        </multi-routing-engine-item>
	        
	    </multi-routing-engine-results>
	    <cli>
	        <banner>{master:0}</banner>
	    </cli>
	</rpc-reply>

#### XML Example 2  

Here we mix in xpath filtering in a commands file, without specifying `-f xml`, and only the lines with xpath expressions will be changed to XML. Take these commands in the file:

	# regular command
	show version

	# xpath filtered
	show route 0.0.0.0 % //rt-entry

	# regular command again
	show route | match 0.0.0.0

	# and xpath filtered again
	show version % //package-information

Here is the output from the device, with the proper lines changed to XML output:

	$ jaide  -i 172.25.1.21 -u root -p root123 operational ~/Desktop/oplist.txt 
	==================================================
	Results from device: 172.25.1.21
	> show version

	fpc0:
	--------------------------------------------------------------------------
	Hostname: Sterling-21-R6
	Model: ex4200-24t
	JUNOS Base OS boot [12.3R3.4]
	JUNOS Base OS Software Suite [12.3R3.4]
	JUNOS Kernel Software Suite [12.3R3.4]
	JUNOS Crypto Software Suite [12.3R3.4]
	JUNOS Online Documentation [12.3R3.4]
	JUNOS Enterprise Software Suite [12.3R3.4]
	JUNOS Packet Forwarding Engine Enterprise Software Suite [12.3R3.4]
	JUNOS Routing Software Suite [12.3R3.4]
	JUNOS Web Management [12.3R3.4]
	JUNOS FIPS mode utilities [12.3R3.4]

	> show route 0.0.0.0 | display xml % //rt-entry
	<rt-entry xmlns:junos="http://xml.juniper.net/junos/12.3R3/junos">
	  <active-tag>*</active-tag>
	  <current-active/>
	  <last-active/>
	  <protocol-name>Static</protocol-name>
	  <preference>5</preference>
	  <age junos:seconds="4559379">7w3d 18:29:39</age>
	  <nh>
	    <selected-next-hop/>
	    <to>172.25.1.1</to>
	    <via>me0.0</via>
	  </nh>
	</rt-entry>


	> show route | match 0.0.0.0

	0.0.0.0/0          *[Static/5] 7w3d 18:29:40

	> show version | display xml % //package-information
	<package-information>
	  <name>junos</name>
	  <comment>JUNOS Base OS boot [12.3R3.4]</comment>
	</package-information>
	<package-information>
	  <name>jbase</name>
	  <comment>JUNOS Base OS Software Suite [12.3R3.4]</comment>
	</package-information>
	<package-information>
	  <name>jkernel-ex</name>
	  <comment>JUNOS Kernel Software Suite [12.3R3.4]</comment>
	</package-information>
	<package-information>
	  <name>jcrypto-ex</name>
	  <comment>JUNOS Crypto Software Suite [12.3R3.4]</comment>
	</package-information>
	<package-information>
	  <name>jdocs-ex</name>
	  <comment>JUNOS Online Documentation [12.3R3.4]</comment>
	</package-information>
	<package-information>
	  <name>jswitch-ex</name>
	  <comment>JUNOS Enterprise Software Suite [12.3R3.4]</comment>
	</package-information>
	<package-information>
	  <name>jpfe-ex42x</name>
	  <comment>JUNOS Packet Forwarding Engine Enterprise Software Suite [12.3R3.4]</comment>
	</package-information>
	<package-information>
	  <name>jroute-ex</name>
	  <comment>JUNOS Routing Software Suite [12.3R3.4]</comment>
	</package-information>
	<package-information>
	  <name>jweb-ex</name>
	  <comment>JUNOS Web Management [12.3R3.4]</comment>
	</package-information>
	<package-information>
	  <name>fips-mode-powerpc</name>
	  <comment>JUNOS FIPS mode utilities [12.3R3.4]</comment>
	</package-information>


# Working with Pipes  

Pipes are a valuable tool for modifying the output received from an operational mode command. Unfortunately because of their uses in a terminal environment, they need to be properly escaped when used with jaide.py.  

**Note** - You should always be aware of your operating system environment and what escape characters are needed. A little bit of trial and error might be needed. We'll give as much information as we can for OS X and Windows here.  

Before we get started, know that an extensive document on all the pipe commands can be found at the **[Junos Pipe Reference](http://www.juniper.net/techpubs/en_US/junos14.1/topics/concept/junos-cli-pipe-filter-functions-overview.html)**.  

### Mac OS X Examples  

#### Mac Pipe Example 1  

To use Jaide to show the terse interface output, filtering out down interfaces, you can do the following (note that since the command is quoted on the command line, the pipe does not need to be escaped):

	$ jaide -i 172.25.1.21 -u root -p root123 operational "show int terse | except down"
	==================================================
	Results from device: 172.25.1.21
	> show int terse | except down

	Interface               Admin Link Proto    Local                 Remote
	ge-0/0/0                up    up
	                                   inet6    2007::1/126     
	                                            fe80::219:e2ff:fe51:85c9/64
	ge-0/0/9                up    up
	ge-0/0/9.0              up    up   eth-switch
	ge-0/0/13               up    up
	ge-0/0/13.0             up    up   eth-switch
	                                   inet6    2008:4498::e/126
	                                            fe80::219:e2ff:fe51:85d2/64
	bme0                    up    up
	bme0.32768              up    up   inet     128.0.0.1/2     
	                                            128.0.0.16/2    
	                                            128.0.0.32/2    
	                                   tnp      0x10            
	dsc                     up    up
	gre                     up    up
	ipip                    up    up
	lo0                     up    up
	lo0.0                   up    up   inet     7.7.7.7/24      
	                                            8.8.8.8/24      
	                                            10.42.0.106         --> 0/0
	                                   inet6    2006::3000:6    
	                                            fe80::219:e20f:fc51:85c0
	lo0.16384               up    up   inet     127.0.0.1           --> 0/0
	lsi                     up    up
	me0                     up    up
	me0.0                   up    up   inet     172.25.1.21/24  
	mtun                    up    up
	pimd                    up    up
	pime                    up    up
	tap                     up    up
	vlan                    up    up

#### Mac Pipe Example 2  

To get more complicated, if you wanted to capture only interfaces that were not down, and included `ge-`, you would do the following: 

	$ jaide -i 172.25.1.21 -u root -p root123 operational "show int terse | except down | match ge-"
	==================================================
	Results from device: 172.25.1.21
	> show int terse | except down | match ge-

	ge-0/0/0                up    up
	ge-0/0/9                up    up
	ge-0/0/9.0              up    up   eth-switch
	ge-0/0/13               up    up
	ge-0/0/13.0             up    up   eth-switch

Note that the above example lost the IP information configured on ge-0/0/0 and ge-0/0/13 since those lines did not match `ge-`.  

#### Mac Pipe Example 3  

Here is an example matching the `ge-` or `lo0` interfaces. Note the need to escape the quotations, since we require quotations within a quote. 

	$ jaide -i 172.25.1.21 -u root -p root123 operational "show int terse | match \"ge-|lo0\""
	==================================================
	Results from device: 172.25.1.21
	> show int terse | match "ge-|lo0"

	ge-0/0/0                up    up
	ge-0/0/1                up    down
	ge-0/0/1.0              up    down inet    
	ge-0/0/2                down  down
	ge-0/0/2.0              up    down inet    
	ge-0/0/3                up    down
	ge-0/0/3.0              up    down inet    
	ge-0/0/4                up    down
	ge-0/0/4.0              up    down inet    
	ge-0/0/5                up    down
	ge-0/0/5.0              up    down inet    
	ge-0/0/6                up    down
	ge-0/0/6.0              up    down inet     77.77.77.1/30   
	ge-0/0/7                up    down
	ge-0/0/7.0              up    down inet    
	ge-0/0/8                up    down
	ge-0/0/9                up    up
	ge-0/0/9.0              up    up   eth-switch
	ge-0/0/10               up    down
	ge-0/0/10.0             up    down inet    
	ge-0/0/11               up    down
	ge-0/0/11.0             up    down inet    
	ge-0/0/12               up    down
	ge-0/0/12.0             up    down inet     172.30.1.220/24 
	ge-0/0/13               up    up
	ge-0/0/13.0             up    up   eth-switch
	ge-0/0/14               up    down
	ge-0/0/14.0             up    down inet    
	ge-0/0/15               up    down
	ge-0/0/15.0             up    down inet     172.27.0.14/30  
	ge-0/0/16               up    down
	ge-0/0/16.0             up    down inet    
	ge-0/0/17               up    down
	ge-0/0/17.0             up    down inet    
	ge-0/0/18               up    down
	ge-0/0/18.0             up    down inet     192.168.246.178/28
	ge-0/0/19               up    down
	ge-0/0/19.0             up    down inet    
	ge-0/0/20               up    down
	ge-0/0/20.0             up    down inet    
	ge-0/0/21               up    down
	ge-0/0/21.0             up    down inet    
	ge-0/0/22               up    down
	ge-0/0/22.0             up    down inet     1.1.1.1/30      
	ge-0/0/23               up    down
	lo0                     up    up
	lo0.0                   up    up   inet     7.7.7.7/24      
	lo0.16384               up    up   inet     127.0.0.1           --> 0/0

Since Junos only recognizes double quotation marks for pipe match statements, but Mac OS X will allow single quotation marks, you could get the same output using the following command, which doesn't require any escaping:  

	$ jaide -i 172.25.1.21 -u root -p root123 operational 'show int terse | match "ge-|lo0"'

### Windows 7 examples

#### Windows Pipe Example 1  

For starters the first command is the same on Windows as it is on Mac OS X:  

	> jaide -u root -p root123 -i 172.25.1.21 operational "show int terse | except down"
	==================================================
	Results from device: 172.25.1.21
	> show int terse | except down

	Interface               Admin Link Proto    Local                 Remote
	ge-0/0/0                up    up
	                                   inet6    2007::1/126
	                                            fe80::219:e2ff:fe51:85c9/64
	ge-0/0/9                up    up
	ge-0/0/9.0              up    up   eth-switch
	ge-0/0/13               up    up
	ge-0/0/13.0             up    up   eth-switch
	                                   inet6    2008:4498::e/126
	                                            fe80::219:e2ff:fe51:85d2/64
	bme0                    up    up
	bme0.32768              up    up   inet     128.0.0.1/2
	                                            128.0.0.16/2
	                                            128.0.0.32/2
	                                   tnp      0x10
	dsc                     up    up
	gre                     up    up
	ipip                    up    up
	lo0                     up    up
	lo0.0                   up    up   inet     7.7.7.7/24
	                                            8.8.8.8/24
	                                            10.42.0.106         --> 0/0
	                                   inet6    2006::3000:6
	                                            fe80::219:e20f:fc51:85c0
	lo0.16384               up    up   inet     127.0.0.1           --> 0/0
	lsi                     up    up
	me0                     up    up
	me0.0                   up    up   inet     172.25.1.21/24
	vlan                    up    up

#### Windows Pipe Example 2  

The second command also runs in the same manner on Windows as compared to OS X:  

	> jaide -u root -p root123 -i 172.25.1.21 operational "show int terse | except down | match ge-"
	==================================================
	Results from device: 172.25.1.21
	> show int terse | except down | match ge-

	ge-0/0/0                up    up
	ge-0/0/9                up    up
	ge-0/0/9.0              up    up   eth-switch
	ge-0/0/13               up    up
	ge-0/0/13.0             up    up   eth-switch

#### Windows Pipe Example 3  

The third command operates a little differently on Windows, the inner pair of quotes must be double stacked for Windows to pass them through to Jaide. The outer quotes cannot be single quotation marks (') on Windows either, so the following is the best method:  

	> jaide -u root -p root123 -i 172.25.1.21 operational "show int terse | match ""ge-|lo0"""
	==================================================
	Results from device: 172.25.1.21
	> show int terse | match "ge-|lo0"

	ge-0/0/0                up    up
	ge-0/0/1                up    down
	ge-0/0/1.0              up    down inet
	ge-0/0/2                down  down
	ge-0/0/2.0              up    down inet
	ge-0/0/3                up    down
	ge-0/0/3.0              up    down inet
	ge-0/0/4                up    down
	ge-0/0/4.0              up    down inet
	ge-0/0/5                up    down
	ge-0/0/5.0              up    down inet
	ge-0/0/6                up    down
	ge-0/0/6.0              up    down inet     77.77.77.1/30
	ge-0/0/7                up    down
	ge-0/0/7.0              up    down inet
	ge-0/0/8                up    down
	ge-0/0/9                up    up
	ge-0/0/9.0              up    up   eth-switch
	ge-0/0/10               up    down
	ge-0/0/10.0             up    down inet
	ge-0/0/11               up    down
	ge-0/0/11.0             up    down inet
	ge-0/0/12               up    down
	ge-0/0/12.0             up    down inet     172.30.1.220/24
	ge-0/0/13               up    up
	ge-0/0/13.0             up    up   eth-switch
	ge-0/0/14               up    down
	ge-0/0/14.0             up    down inet
	ge-0/0/15               up    down
	ge-0/0/15.0             up    down inet     172.27.0.14/30
	ge-0/0/16               up    down
	ge-0/0/16.0             up    down inet
	ge-0/0/17               up    down
	ge-0/0/17.0             up    down inet
	ge-0/0/18               up    down
	ge-0/0/18.0             up    down inet     192.168.246.178/28
	ge-0/0/19               up    down
	ge-0/0/19.0             up    down inet
	ge-0/0/20               up    down
	ge-0/0/20.0             up    down inet
	ge-0/0/21               up    down
	ge-0/0/21.0             up    down inet
	ge-0/0/22               up    down
	ge-0/0/22.0             up    down inet     1.1.1.1/30
	ge-0/0/23               up    down
	lo0                     up    up
	lo0.0                   up    up   inet     7.7.7.7/24
	lo0.16384               up    up   inet     127.0.0.1           --> 0/0
