Working with Pipes
==================

Pipes are a valuable tool for modifying the output received from an operational mode command. Unfortunately because of their uses in a terminal environment, they need to be properly escaped when used with jaide.py.  

**Note** - You should always be aware of your operating system environment and what escape characters are needed. A little bit of trial and error might be needed. We'll give as much information as we can for OS X and Windows here.  

Before we get started, know that an extensive document on all the pipe commands can be found at the **[Junos Pipe Reference](http://www.juniper.net/techpubs/en_US/junos14.1/topics/concept/junos-cli-pipe-filter-functions-overview.html)**.  

#### For JGUI
Luckily for JGUI users there is no special consideration for pipes at all. When entering operational mode commands with pipes, enter them exactly as you would into Junos directly, meaning if doing `match` with OR statements, double-quotation marks are required to wrap the OR statement: `show int terse | match "ge-|lo0" | except 1`. 

#### Mac OS X examples

To use Jaide to show the terse interface output, filtering out down interfaces, you can do the following (note that since the command is quoted on the command line, the pipe does not need to be escaped):

	$ python jaide.py -u root -p root123 -c "show int terse | except down" -i 172.25.1.21
	==================================================
	Results from device: 172.25.1.21
	> show int terse | except down | no-more

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

To get more complicated, if you wanted to capture only interfaces that were not down, and included `ge-`, you would do the following: 

	$ python jaide.py -u root -p root123 -c "show int terse | except down | match ge-" -i 172.25.1.21
	==================================================
	Results from device: 172.25.1.21
	> show int terse | except down | match ge- | no-more

	ge-0/0/0                up    up
	ge-0/0/9                up    up
	ge-0/0/9.0              up    up   eth-switch
	ge-0/0/13               up    up
	ge-0/0/13.0             up    up   eth-switch

Note that the above example lost the IP information configured on ge-0/0/0 and ge-0/0/13 since those lines did not match have `ge-`.  

Here is an example matching the `ge-` or `lo0` interfaces. Note the need to escape the quotations, since we require quotations within a quote. 

	$ python jaide.py -u root -p root123 -c "show int terse | match \"ge-|lo0\"" -i 172.25.1.21
	==================================================
	Results from device: 172.25.1.21
	> show int terse | match "ge-|lo0" | no-more

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

	$ python jaide.py -u root -p root123 -c 'show int terse | match "ge-|lo0"' -i 172.25.1.21

#### Windows 7 examples

For starters the first command is the same on Windows as it is on Mac OS X:  

	>python jaide.py -u root -p root123 -i 172.25.1.21 -c "show int terse | except down"
	==================================================
	Results from device: 172.25.1.21
	> show int terse | except down | no-more

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

The second command also runs in the same manner on Windows as compared to OS X:  

	>python jaide.py -u root -p root123 -i 172.25.1.21 -c "show int terse | except down | match ge-"
	==================================================
	Results from device: 172.25.1.21
	> show int terse | except down | match ge- | no-more

	ge-0/0/0                up    up
	ge-0/0/9                up    up
	ge-0/0/9.0              up    up   eth-switch
	ge-0/0/13               up    up
	ge-0/0/13.0             up    up   eth-switch

The third command operates a little differently on Windows, the inner pair of quotes must be double stacked for Windows to pass them through to Jaide. The outer quotes cannot be single quotation marks (') on Windows either, so the following is the best method:  

	>python jaide.py -u root -p root123 -i 172.25.1.21 -c "show int terse | match ""ge-|lo0"""
	==================================================
	Results from device: 172.25.1.21
	> show int terse | match "ge-|lo0" | no-more

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
