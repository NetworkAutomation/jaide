Redirecting output to file  
==========================  

When using the any command line utility, you always have the OS integrated option of redirecting the output of the command to a file using the `>` operator. However, using the Jaide CLI built in `-w` option, you get a little bit more flexibility by being able to redirect output from each device to a separate file.  

The `-w` option expects two arguments: `MODE` and `FILEPATH`. The format is as follows:  

	jaide -w MODE FILEPATH COMMAND [ARGS]  

The MODE must be one of the following options:  

* `s` or `single`. Write all output from all devices to the same file.  
* `m` or `multiple`. Write the output from each device to it's own file.  

The naming convention used when writing to multiple files is: 

	DEVICE_IP + _ + FILENAME  

The device IP will be whatever was used to connect to the device (IP address, hostname) and the filename is what was specified as the second argument to the `-w` option.  

Here is an example:  

	$ jaide -i 172.25.1.1,firewall.hostname.com,192.168.1.3 -u username -p password -w m /var/tmp/version_output.txt operational "show version"  

This would produce the following files in the /var/tmp/ folder:  

	172.25.1.1_version_output.txt
	firewall.hostname.com_version_output.txt
	192.168.1.3_version_output.txt