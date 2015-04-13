Working with Custom Timeout Values
==================================

## Session Timeout  

The timeout argument `-t`/`--session-timeout` can be used to modify the default timeout value of 300 seconds for the session to the Junos device(s). This can be useful if you are running a command that you know will take longer than 300 seconds to execute before you see any return.  

A known example of when this is necessary is the command `request system snapshot slice alternate` to copy the booted partition to the backup partition. The snapshot command will not give any feedback for 15+ minutes depending on the model that the command was executed on. If the timeout value was left at the default value of 300 seconds, the jaide CLI tool would close the connection to the device before the snapshot command completed, potentially causing problems.  

	$ jaide -i 172.25.1.21 -t 7200 operational "request system snapshot slice alternate"

**Note -** We have used this command in our testing experience to ensure that it works. However, always take caution when executing any commands that could potentially harm the networking device or the network configuration. We are not responsible for mis-use of this tool!  

## Connect Timeout

There is another timeout option, `-T`/`--connect-timeout`, which can be used to increase the default 5 second timer when connecting to a device intially. If this time value runs out, we consider the device unreachable during connection establishment, and a Jaide error will be shown: 

	$ jaide  -i 172.25.1.112 -u root -p root123 info
	==================================================
	Results from device: 172.25.1.112

	Timeout exceeded connecting to device: 172.25.1.112

