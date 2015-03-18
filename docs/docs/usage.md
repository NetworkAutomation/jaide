Basic Usage  
===========  

TODO: update links  
This page is for Basic usage of both the CLI tool and the Jaide library. Expansive information can be found in the respective sections of the [documentation](READ THE DOCS page).  

## Jaide CLI tool  
If you installed jaide, you automatically have access to the `jaide` command anywhere in any terminal/command prompt on your machine. There are many options and commands to use with the Jaide CLI tool. The basic usage is as follows:  

`jaide [options] COMMAND [options | ARGS]`  

**Note** The majority of this information is available by using the built in command line help, which can be accessed through:  
`jaide -h` for generic help and `jaide COMMAND -h` for command-specific help/options.  

#### Basic Jaide Options  
The first set of options (the first `[options]` instance in the command usage string above) contain the following possibilities:

| Option | Full Option Flag | Type | Description |
| ------ | ---------------- | ---- | ----------- |
| -h 	 | --help  			| N/A  | Print the basic help information for Jaide and exit. |  
| -i 	 | --ip 			| TEXT | The target hostname(s) or IP(s). **[1](#notes)** Will prompt if not in the command line arguments. |  
| -p 	 | --password 		| TEXT | The password for authenticating to the device(s). Will prompt if not in the command line arguments. |  
| -P 	 | --port 			| INTEGER | The port to connect to the device on. Defaults to port 22 (SSH) |  
| --quiet | --no-quiet 	| N/A | Boolean flag for suppressing all output from the script. Defaults to False (--no-quiet) |  
| -t 	  | --session-timeout | INTEGER | The session timeout, in seconds, for declaring a lost session. Default is 300 seconds. This should be increased when no return output could be seen for more than 5 minutes (for example requesting a system snapshot). |  
| -T 	 | --connect-timeout | INTEGER | The timeout, in seconds, for declaring a device unreachable during connection establishment. Defaults to 5 seconds. |  
| -u | --username | TEXT | The username for authenticating to the device(s). Will prompt if not in the command line arguments. |  
| N/A | --version | N/A | Print the version of the jaide script (and jaide package) and exit. |  
| -w | --write | TEXT FILEPATH | Write the output to one or multiple files, instead of printing to stdout. Useful when touching more than one device, as the 'm' or 'multiple' options will write the output for each device to a separate file. [More info here](#TODO: WRITE TO FILE DOC LINK) |  

These are the available commands in the jaide CLI tool:  

| Command | Description |  
| ------- | ----------- |  
| commit  | Execute a commit operation. **[1](#notes)** Several options exist for further customization, such as confirming, commit check, comments, etc. |  
| compare | Run a 'show pipe compare' for a list of set commands. **[1](#notes)** |  
| diff_config | Compare the configuration differences between two devices. |  
| errors | Get any interface errors from any interface. |  
| health | Get alarm, CPU, RAM, and temperature status. |  
| info | Get basic device information, such as version, model, hostname, serial number, and uptime. |  
| operational | Send operational command(s) and display the output. **[1](#notes)** Pipes are supported, as well as xpath filtering **[2](#notes).** |  
| pull | Copy files from the device(s) to the local machine. |  
| push | Copy files from the local machine to the device(s). |  
| shell | Send shell command(s) and display the output. **[1](#notes)** |  

More information on each of the above commands can be found in each of their CLI usage guides.
#### Example Jaide Commands:
Check the target IP for interface errors on all its up/up interfaces, it will prompt for authentication.  
`jaide -i 10.2.10.12 errors`  

Backup the primary partition to the backup slice, increasing the timeout value so the connection doesn't time out waiting for the response.  
`jaide -i 10.10.10.10 -t 7200 op 'request system snapshot slice alternate'`  

Send a list of set commands and commit them to a list of IPs, without being prompted for username/password.  
`jaide -u user -p mypassword -i /var/iplist.txt commit "~/Desktop/list_of_set_commands.txt"`  

SCP push the local code file */code/jinstall-ex-2200.tgz* file to an IP list and put it in the */var/tmp* folder.  
`jaide -u user -p mypassword -i /var/iplist.txt push /code/jinstall-ex-2200.tgz /var/tmp/`  

SCP pull the remote */var/tmp* directory on an IP list to the local */Users/self/Desktop/IPaddress_tmp* folders.  
`jaide -u user -p mypassword -i /var/iplist.txt pull /var/tmp /Users/self/Desktop/`  

Send a blank commit.  
`jaide -u user -p mypassword -i 10.0.0.123 commit --blank`  

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

# Change devices:
session.host = '172.16.2.2'
session.username = 'myusername'
session.password = 'different_password'

# Pull a file down, and echo back the live progress
session.scp_pull('/var/log/messages', '/path/to/local/folder', progress=True)  

# Perform a commit check operation for a set command to see if it passes syntax
print session.commit_check(commands='set interfaces ge-0/0/0 description asdf')  

# Commit a file of set commands, with a comment, and set to roll back in 10 minutes.
print session.commit(commands='/path/to/file/of/set/commands', comment='Making a commit', confirmed=600)  

# Confirm the commit (prints the text response from the device, in this case 'commit complete')
print session.commit()

session.disconnect()  
```

## Notes  
* 1) There are multiple ways to specify these pieces of information (Hostnames/IPs, op commands, shell commands, set commands). It can be a single instance, multiple in a quoted comma-separated list, or a filepath pointing to a file with one entry on each line. More information is in their respective detailed docs.  
* 2) Pipes are very powerful, and should be learned for advanced command usage in [Junos natively](http://www.juniper.net/techpubs/en_US/junos14.2/topics/concept/junos-cli-pipe-filter-functions-overview.html). Xpath filtering is an added feature of Jaide, and can be learned of in our [operational command guide](#TODO: operational command guide link).  