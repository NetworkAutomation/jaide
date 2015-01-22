Working with XML and XPATH
==================

The (-f/--format) argument can be used to retrieve XML output from the device instead of text output. This can be useful for many reasons, including writing SLAX scripts or other automation purposes. 

With or without `-f xml`, you can include a xpath expression to filter the returned XML output. Simply append `% xpath_expression` to the end of an operational command to filter the output and force an XML response. For example: `show version % //package-information` returns all the <package-information> nodes in the XML response to `show version | display xml`. This is shown below in the second example where alternating commands with and without xpath filters are sent, and only the ones with xpath expressions are returned in XML output, the rest are text.

#### For JGUI
For JGUI, we have built the `Request XML Format` checkbox for operational commands that will force `-f xml` for all commands. You can also use the '% xpath_expression' at the end of any operational command to force xml, and xpath filter the output, without changing the format to xml for any other commands run as well.

#### Examples

Here we simply change the output format of the `show version` command to be xml.  

	$ python jaide.py -f xml -i 172.25.1.21 -u root -c "show version"
	==================================================
	Results from device: 172.25.1.21
	> show version | display xml | no-more

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

Here we mix in xpath filtering in a commands file, without specifying -f xml, and only the lines with xpath expressions will be changed to xml. Take these commands in the file:

	# regular command
	show version

	# xpath filtered
	show route 0.0.0.0 % //rt-entry

	# regular command again
	show route | match 0.0.0.0

	# and xpath filtered again
	show version % //package-information

Here is the output from the device, with the proper lines changed to xml output:

	$ python jaide.py  -i 172.25.1.21 -u operate -c ~/Desktop/oplist.txt 
	==================================================
	Results from device: 172.25.1.21
	> show version | no-more

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

	> show route 0.0.0.0 | display xml | no-more % //rt-entry
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


	> show route | match 0.0.0.0 | no-more

	0.0.0.0/0          *[Static/5] 7w3d 18:29:40
	10.0.0.0/24        *[Static/5] 7w3d 18:29:40

	> show version | display xml | no-more % //package-information
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
