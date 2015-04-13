Comparing Set Commands  
======================  

When editing the configuration of a Junos device through the CLI, Junos gives you the ability to do a `show | compare` to see the changes you have submitted that will take effect when you commit. This is possible in jaide by using the `compare` command.  

One argument is required for this command, which is the set command(s) that will be tested. Much like IPs, op commands, and shell commands, this can also be a comma separated list or a filepath to a list of commands on each line.  

#### Example: 

	$ jaide  -i 192.168.50.95 -u root -p root123 compare "set interfaces ge-0/0/0 description asdfqwe, set vlans v123 vlan-id 123"
	==================================================
	Results from device: 192.168.50.95

	show | compare:

	[edit interfaces ge-0/0/0]
	+   description asdfqwe;
	[edit vlans v123]
	+   vlan-id 123;

