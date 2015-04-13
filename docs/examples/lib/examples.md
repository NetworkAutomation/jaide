The Jaide class library  
=======================  

Extended documentation on the available properties and functions of the Jaide class are available in the [API section](/api/api) of the documentation.  

## Basic example  

Instantiating a Jaide object and manipulating a junos device can be quite easy:  
```python  
from jaide import Jaide

# Create the Jaide object, which opens a connection
session = Jaide('172.16.1.1', 'username', 'password')  

# Run an operational command
print session.op_cmd('show interfaces terse')  

# Disconnect
session.disconnect()
```  

## Extended example  

You can also chain commands together and redirect Jaide at a new host:  
```python
from jaide import Jaide

# Create the Jaide object, which opens a connection
session = Jaide('172.16.1.1', 'username', 'password')  

# Run a file of shell commands
print session.shell_cmd('/path/to/file/of/shell/commands')  

# Change devices. This doesn't connect to the new device until a command is executed
session.host = '172.16.2.2'
session.username = 'new_username'
session.password = 'different_password'

# Now the connection would be redirected to the new device on the next line.
# Perform a commit check operation for a set command to see if it passes syntax
print session.commit_check(commands='set interfaces ge-0/0/0 description asdf')  

# Pull a file down, and echo back the live progress
# Notice `print` is not needed because flagging progress=True automatically prints to stdout.
session.scp_pull('/var/log/messages', '/path/to/local/folder', progress=True)  

# Commit a file of set commands, with a comment, and set to roll back in 10 minutes.
print session.commit(commands='/path/to/file/of/set/commands', comment='Making a commit', confirmed=600)  

# Confirm the commit (prints the text response from the device, in this case 'commit complete')
print session.commit()

session.disconnect()  
```
