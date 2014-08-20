Working with custom timeout values
==================================

The timeout argument `-t` can be used to modify the default timeout value of 300 seconds for the session to the Junos device(s). This can be useful if you are running a command that you know will take longer than 300 seconds to execute before you see any return.  

A known example of when this is necessary is the command `request system snapshot slice alternate` to copy the booted partition to the backup partition. The snapshot command will not give any feedback for 15+ minutes depending on the model that the command was executed on. If the timeout value was left at the default value of 300 seconds, the jaide.py script would close the connection to the device before the snapshot command completed, potentially ruining the alternate partition.  

	$ python jaide.py -i 172.25.1.21 -c "request system snapshot slice alternate" -t 1800

**Note -** We have used this command in our testing experience to ensure that it works. However, always take caution when executing any commands that could potentially harm the networking device or the network configuration. We are not responsible for mis-use of this script!