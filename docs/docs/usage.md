Basic Usage  
===========  

## Jaide CLI tool  
There are many combinations of arguments that can be used to perform all functions available using the Jaide.py command line tool. Two arguments are always required: the `-i` target device(s), and one of the arguments for performing a given function [ -b | -c | -e | --health | --info | -s | --scp | --shell ]. These functions are detailed below in the second table. 

**A destination IP or IP list is required:**  The script will accept a single IP address, a quoted comma separated list, or a file with a list of IPs, separated by newlines. DNS hosts will work as well; resolution uses your machine's specified DNS server(s).  

| Single | Comma Separated List | Filepath |  
| ------ | -------------------- | -------- |  
| `-i/--ip ip.add.re.ss` | `-i/--ip "ip.add.re.ss1, ip.add.re.ss2, DNS.entry.com"` | `-i/--ip /path/to/file/of/ip/addresses.txt` |  

These are the main operations that can be performed. **One and only one of the following is required:**  

| Argument | Description |  
| -------- | ----------- |  
| `-c/--command "quoted operational mode command(s)"` | Send a single operational mode command, a comma separated list of commands, or a filepath to a file containing commands on each line. Can include `show`, `request`, `traceroute`, op scripts, etc. |  
| `-e/--errors` | Check all up/up ports for interface errors |  
| `-H/--health` | Pull a health check from the device |  
| `-I/--info` | Retrieve basic device information (Serial, model, etc) |  
| `-s/--set "quoted set command(s)"` | Send a single set command, a quoted comma separated list of commands, or specify a file containing one set command on each line. |  
| `-b/--blank` | Make a commit with no set commands, a 'commit blank'. Useful for confirming a commit confirmed. |  
| `-S/--scp [push OR pull] /source/file/or/folder /destination/file/or/folder` | SCP push or pull operation |  
| `-l/--shell "quoted shell command(s)"` | Similar to `-c`, except it will run shell commands. |  
 
Authentication arguments are optional on the command line. If they are not provided the script will prompt for them, with the benefit of the password not being echoed to the user.  

| Argument | Description |  
| -------- | ----------- |  
| `-u/--username USERNAME` | The username for the device connection(s) |  
| `-p/--password PASSWORD` | The password for the device connection(s) |  
  
The `-s` argument can take one or none of the three following optional arguments for changing the commit type:  

| Argument | Description |  
| -------- | ----------- |  
| `-m/--confirm INTEGER_OF_MINUTES` | Will change the commit operation to a commit confirmed for the integer_of_minutes length of time  |  
| `-k/--check` | Instead of committing, this will do a 'commit check' and return the output, letting you know if it passed or not, and why.  | 
  
Other optional arguments:  

| Argument | Description |  
| -------- | ----------- |  
| `-f/--format [text OR xml]` | This changes the output of the command returned from the device. It defaults to 'text', and will only take effect on operational mode commands. With or without -f, you can do xpath filtering, by putting ` % XPATH_EXPRESSION` after your operational command. For example: `show route % //rt-entry`. |  
| `-q/--quiet` | Used in conjunction with `-S/--scp`, when copying to/from a single device, to prevent seeing the callback status of the transfer as it happens. |  
| `-t/--timeout INTEGER_OF_SECONDS` | Will change the timeout for operation sent to the device. Defaults to 300 seconds. Check the help file for timeout. |  
| `-w/--write s/single_OR_m/multiple OUTPUT_FILENAME` | Write the output of the script to a file(s). `-w s ~/Desktop/output.txt` will write all output to one file, whereas `-w multiple ~/Desktop/output.txt` will write one file for each device connecting to, resulting in `~/Desktop/IP_OF_DEVICE_output.txt` being written for each device. |  

#### Example jaide commands:
Check the target IP for interface errors on all its up/up interfaces, it will prompt for authentication.  
`jaide -i 10.2.10.12 -e`

Backup the primary partition to the backup slice, increasing the timeout value so the NCClient connection doesn't get lost.  
`jaide -i 10.10.10.10 -c 'request system snapshot slice alternate' -t 1800`

Send a list of set commands and commit them to a list of IPs, without being prompted for username/password.  
`jaide -u user -p mypassword -i ~/Downloads/iplist.txt -s ~/Desktop/list_of_set_commands.txt`

SCP push the local code file *~/Downloads/jinstall-ex-2200-12.3R3.4-domestic-signed.tgz* file to an IP list and put it in the */var/tmp* folder.  
`jaide -u user -p mypassword -i ~/Downloads/iplist.txt --scp push ~/Downloads/jinstall-ex-2200-12.3R3.4-domestic-signed.tgz /var/tmp/`

SCP pull the remote */var/tmp* directory on an IP list to the local *~/Desktop/IPaddress_tmp* folders.  
`jaide -u user -p mypassword -i ~/Downloads/iplist.txt --scp pull /var/tmp ~/Desktop/`  

Send a blank commit.  
`jaide -u user -p mypassword -i 10.0.0.123 --blank`  

## Using the Jaide class  

Instantiating a Jaide object and manipulating a junos device can be quite easy:  
```python  
from jaide import Jaide

# Create the Jaide object, which opens a connection
session = Jaide('172.16.1.1', 'username', 'password')  

# Run an operational command
print session.op_cmd('show interfaces terse')  

# Run a file of shell commands
print session.shell_cmd('/path/to/file/of/shell/commands')  

# Pull a file down, and echo back the progress
session.scp_pull('/var/log/messages', '/path/to/local/folder', progress=True)  

# Perform a commit check operation for a set command to see if it passes
print session.commit_check('set interfaces ge-0/0/0 description asdf')  

# Commit a file of set commands, with a comment, and set to roll back in 10 minutes.
print session.commit('/path/to/file/of/set/commands', comment='Making a commit', confirmed=600)  

session.disconnect()  
```