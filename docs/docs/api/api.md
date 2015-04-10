API Reference  
============  

## Jaide Class  
*class* **Jaide**(): 
>  __Purpose__: An object for manipulating a Junos device.
> 
> Methods include copying files, running show commands,
> shell commands, commit configuration changes, finding
> interface errors, and getting device status/information.
> 
> All of the methods listed below that touch Junos are wrapped by a
> decorator function @check_instance, which handles ensuring the correct
> connection is used to perform the requested operation.

**\_\_init\_\_**(*self, host, username, password, connect_timeout=5, session_timeout=300, connect="paramiko", port=22*):
>  Initialize the Jaide object.
> 

> __Purpose:__ This is the initialization function for the Jaide class,
> which creates a connection to a junos device. It will
> return a Jaide object, which can then be used to actually
> send commands to the device. This function establishes the
> connection to the device via a NCClient manager object.
> > **NOTE:** The connect parameter should be ignored under most
> > circumstances. Changing it only affects how Jaide first
> > connects to the device. The decorator function
> > @check_instance will handle moving between session
> > types for you.
> 
> * __host__: The IP or hostname of the device to connect to.
>   1. _Type_: str
> * __username__: The username for the connection
>   1. _Type_: str
> * __password__: The password for the connection
>   1. _Type_: str
> * __connect_timeout__: The timeout value, in seconds, for attempting
> to connect to the device.
>   1. _Type_: int
> * __session_timeout__: The timeout value, in seconds, for the
> session. If a command is sent and nothing
> is heard back from the device in this
> timeframe, the session is declared dead,
> and times out.
>   1. _Type_: int
> * __connect__: **NOTE: We default to 'paramiko', but this
> parameter can be set to False to prevent connecting
> on object instantiation. The @check_instance
> decorator function will handle sliding between
> session types depending on what function is being
> called, meaning generally self.conn_type and this
> connect parameter should be ignored.**
> The connection type that should be made. Several
> options are available: 'ncclient', 'scp', and
> 'paramiko', 'shell' and 'root'.
> 'paramiko' : is used for operational commands
> (couldn't use ncclient because of lack of pipes `|`
> support.
> 'scp' : is used for copying files to/from
> the device, and uses an SCP connection.
> 'shell' : is for sending shell commands.
> 'root' : is when the user is doing operational
> commands, but is logged in as root, (requires
> handling separately, since this puts the session
> into a shell prompt)
> 'ncclient' : is used for all other commands.
>   1. _Type_: str
> * __port__: The destination port on the device to attempt the
> connection.
>   1. _Type_: int
> 

> __Returns__: an instance of the Jaide class
> _Return Type_: jaide.Jaide object

**check_instance**(*function*):
>  Wrapper that tests the type of _session.
> 

> __Purpose:__ This decorator function is used by all functions within
> the Jaide class that interact with a device to ensure the
> proper session type is in use. If it is not, it will
> attempt to migrate _session to that type before moving
> to the originally requested function.
> > **NOTE:** This function is a decorator, and should not be
> >  used directly. All other methods in this class that touch
> >  the Junos device are wrapped by this function to ensure the
> >  proper connection type is used.
> 
> * __function__: the function that is being wrapped around
>   1. _Type_: function
> 

> __Returns__: the originally requested function
> _Return Type_: function

**cli_to_shell**(*self*):
>  Move _shell to the shell from the command line interface (CLI). 

**commit**(*self, commands="", confirmed=None, comment=None, at_time=None, synchronize=False, req_format='text'*):
>  Perform a commit operation.
> 

> __Purpose:__ Executes a commit operation. All parameters are optional.
> commit confirm and commit at are mutually exclusive. All
> the others can be used with each other and commit confirm/at.
> 
> * __commands__: A string or list of multiple commands
> that the device will compare with.
> If a string, it can be a single command,
> multiple commands separated by commas, or
> a filepath location of a file with multiple
> commands, each on its own line.
>   1. _Type_: str or list
> * __confirmed__: integer value of the number of **seconds** to
> confirm the commit for, if requested.
>   1. _Type_: int
> * __comment__: string that the user wants to comment the commit
> with. Will show up in the 'show system commit' log.
>   1. _Type_: str
> * __at_time__: string designating the time at which the commit
> should happen. Can be in one of two Junos approved
> formats.
>   1. _Type_: str
> * __synchronize__: boolean set to true if desiring a commit
> synchronize operation.
>   1. _Type_: bool
> * __req_format__: string to specify the response format. Accepts
> either 'text' or 'xml'
>   1. _Type_: str
> 

> __Returns__: The reply from the device.
> _Return Type_: str

**commit_check**(*self, commands="", req_format="text"*):
>  Execute a commit check operation.
> 

> __Purpose:__ This method will take in string of multiple commands,
> and perform and 'commit check' on the device to ensure
> the commands are syntactically correct. The response can
> be formatted as text or as xml.
> 
> * __commands__: A string, filepath, or list of multiple commands
> that the device will compare with.
>   1. _Type_: str or list
> * __req_format__: The desired format of the response, defaults to
> 'text', but also accepts 'xml'
>   1. _Type_: str
> 

> __Returns__: The reply from the device.
> _Return Type_: str

**compare_config**(*self, commands="", req_format="text"*):
>  Execute a 'show | compare' against the specified commands.
> 

> __Purpose:__ This method will take in string of multiple commands,
> and perform and 'show | compare' on the device to show the
> differences between the active running configuration and
> the changes proposed by the passed commands parameter.
> 
> * __commands__: A string, filepath, or list of multiple commands
> that the device will compare with.
>   1. _Type_: str or list
> * __req_format__: The desired format of the response, defaults to
> 'text', but also accepts 'xml'
>   1. _Type_: str
> 

> __Returns__: The reply from the device.
> _Return Type_: str

**connect**(*self*):
>  Establish a connection to the device.
> 

> __Purpose:__ This method is used to make a connection to the junos
> device. The internal property conn_type is what
> determines the type of connection we make to the device.
> - 'paramiko' is used for operational commands (to allow
>            pipes in commands)
> - 'scp' is used for copying files
> - 'shell' is used for to send shell commands
> - 'root' is used when logging into the device as root, and
>            wanting to send operational commands
> - 'ncclient' is used for the rest (commit, compare_config,
>            commit_check)
> 

> __Returns__: None
> _Return Type_: None

**_copy_status**(*self, filename, size, sent*):
>  Echo status of an SCP operation.
> 

> __Purpose:__ Callback function for an SCP operation. Used to show
> the progress of an actively running copy. This directly
> prints to stdout, one line for each file as it's copied.
> The parameters received by this function are those received from
> the scp.put or scp.get function, as explained in the python
> scp module docs.
>
> * __filename__: The filename of file being copied.
>   1. _Type_: str
> * __size__: The total size of the current file being copied.
>   1. _Type_: str or float
> * __sent__: The amount of data sent for the current file being copied.
>   1. _Type_: str or float
> 

> __Returns__: None

**device_info**(*self*):
>  Pull basic device information.
> 

> __Purpose:__ This function grabs the hostname, model, running version, and
> serial number of the device.
> 

> __Returns__: The output that should be shown to the user.
> _Return Type_: str

**diff_config**(*self, second_host, mode='stanza'*):
>  Generate configuration differences with a second device.
> 

> __Purpose:__ Open a second ncclient.manager.Manager with second_host, and
> and pull the configuration from it. We then use difflib to
> get the delta between the two, and yield the results.
> 
> * __second_host__: the IP or hostname of the second device to
> compare against.
>   1. _Type_: str
> * __mode__: string to signify 'set' mode or 'stanza' mode.
>   1. _Type_: str
> 

> __Returns__: iterable of strings
> _Return Type_: str

**disconnect**(*self*):
>  Close the connection(s) to the device.
> 

> __Purpose:__ Closes the current connection(s) to the device, no matter
> what types exist.
> 

> __Returns__: None
> _Return Type_: None

**_error_parse**(*self, interface, face*):
>  Parse the extensive xml output of an interface and yield errors.
> 

> __Purpose:__ Takes the xml output of 'show interfaces extensive' for a
> given interface and yields the error types that have a
> significant number of errors.
> 
> * __interface__: The xml output of the 'sh int ext' command for
> the desired interface.
>   1. _Type_: lxml.etree._Element object
> * __face__: The direction of the errors we're wanting. Either 'input'
> or 'output' is accepted.
>   1. _Type_: str
> 

> __Returns__: Yields each error that has a significant number
> _Return Type_: iterable of strings.

**health_check**(*self*):
>  Pull health and alarm information from the device.
> 

> __Purpose:__ Grab the cpu/mem usage, system/chassis alarms, top 5
> processes, and states if the primary/backup partitions are on
> different versions.
> 

> __Returns__: The output that should be shown to the user.
> _Return Type_: str

**interface_errors**(*self*):
>  Parse 'show interfaces extensive' and return interfaces with errors.
> 

> __Purpose:__ This function is called for the -e flag. It will let the user
> know if there are any interfaces with errors, and what those
> interfaces are.
> 

> __Returns__: The output that should be shown to the user.
> _Return Type_: str

**lock**(*self*):
>  Lock the candidate config. Requires ncclient.manager.Manager. 

**op_cmd**(*self, command, req_format='text', xpath_expr=""*):
>  Execute an operational mode command.
> 

> __Purpose:__ Used to send an operational mode command to the connected
> device. This requires and uses a paramiko.SSHClient() as
> the handler so that we can easily pass and allow all pipe
> commands to be used.
> We indiscriminately attach ' | no-more' on the end of
> every command so the device doesn't hold output. The
> req_format parameter can be set to 'xml' to force raw
> xml output in the reply.
> 
> * __command__: The single command that to retrieve output from the
> device. Any pipes will be taken into account.
>   1. _Type_: str
> * __req_format__: The desired format of the response, defaults to
> 'text', but also accepts 'xml'. **NOTE**: 'xml'
> will still return a string, not a libxml ElementTree
>   1. _Type_: str
> 

> __Returns__: The reply from the device.
> _Return Type_: str

**scp_pull**(*self, src, dest, progress=False, preserve_times=True*):
>  Makes an SCP pull request for the specified file(s)/dir.
> 

> __Purpose:__ By leveraging the _scp private variable, we make an scp pull
> request to retrieve file(s) from a Junos device.
> 
> * __src__: string containing the source file or directory
>   1. _Type_: str
> * __dest__: destination string of where to put the file(s)/dir
>   1. _Type_: str
> * __progress__: set to `True` to have the progress callback be
> printed as the operation is copying. Can also pass
> a function pointer to handoff the progress callback
> elsewhere.
>   1. _Type_: bool or function pointer
> * __preserve_times__: Set to false to have the times of the copied
> files set at the time of copy.
>   1. _Type_: bool
> 

> __Returns__: `True` if the copy succeeds.
> _Return Type_: bool

**scp_push**(*self, src, dest, progress=False, preserve_times=True*):
>  Purpose: Makes an SCP push request for the specified file(s)/dir.
> 
> * __src__: string containing the source file or directory
>   1. _Type_: str
> * __dest__: destination string of where to put the file(s)/dir
>   1. _Type_: str
> * __progress__: set to `True` to have the progress callback be
> printed as the operation is copying. Can also pass
> a function pointer to handoff the progress callback
> elsewhere.
>   1. _Type_: bool or function pointer
> * __preserve_times__: Set to false to have the times of the copied
> files set at the time of copy.
>   1. _Type_: bool
> 

> __Returns__: `True` if the copy succeeds.
> _Return Type_: bool

**shell_cmd**(*self, command=""*):
>  Execute a shell command.
> 

> __Purpose:__ Used to send a shell command to the connected device.
> This uses the self._shell instance, which should be a
> paramiko.Channel object, instead of a SSHClient.
> This is because we cannot send shell commands to the
> device using a SSHClient.
> 
> * __command__: The single command that to retrieve output from the
> device.
>   1. _Type_: str
> 

> __Returns__: The reply from the device.
> _Return Type_: str

**shell_to_cli**(*self*):
>  Move _shell to the command line interface (CLI). 

**unlock**(*self*):
>  Unlock the candidate config.
> 

> __Purpose:__ Unlocks the candidate configuration, so that other people can
> edit the device. Requires the _session private variable to be
> a type of a ncclient.manager.Manager.


*Property* __host__

*Property* __conn_type__

*Property* __username__

*Property* __password__

*Property* __port__

*Property* __connect_timeout__

*Property* __session_timeout__

## Utility Functions  
jaide.utils.**clean_lines**(*commands*):
>  Generate strings that are not comments or lines with only whitespace.
> 

> __Purpose:__ This function is a generator that will read in either a
> plain text file of strings(IP list, command list, etc), a
> comma separated string of strings, or a list of strings. It
> will crop out any comments or blank lines, and yield
> individual strings.
> Only strings that do not start with a comment '#', or are not
> entirely whitespace will be yielded. This allows a file with
> comments and blank lines for formatting neatness to be used
> without a problem.
> 
> * __commands__: This can be either a string that is a file
> location, a comma separated string of strings
> ('x,y,z,1,2,3'), or a python list of strings.
>   1. _Type_: str or list
> 

> __Returns__: Yields each command in order
> _Return Type_: iterable of str

jaide.utils.**xpath**(*source_xml, xpath_expr, req_format='string'*):
>  Filter xml based on an xpath expression.
> 

> __Purpose:__ This function applies an Xpath expression to the XML
> supplied by source_xml. Returns a string subtree or
> subtrees that match the Xpath expression. It can also return
> an xml object if desired.
> 
> * __source_xml__: Plain text XML that will be filtered
>   1. _Type_: str or lxml.etree.ElementTree.Element object
> * __xpath_expr__: Xpath expression that we will filter the XML by.
>   1. _Type_: str
> * __req_format__: the desired format of the response, accepts string or
> xml.
>   1. _Type_: str
> 

> __Returns__: The filtered XML if filtering was successful. Otherwise,
> an empty string.
> _Return Type_: str or ElementTree


## Color Utility Functions  
jaide.color_utils.**color**(*out_string, color='grn'*):
>  Highlight string for terminal color coding.
> 

> __Purpose:__ We use this utility function to insert a ANSI/win32 color code
> and Bright style marker before a string, and reset the color and
> style after the string. We then return the string with these
> codes inserted.
> 
> * __out_string__: the string to be colored
>   1. _Type_: str
> * __color__: a string signifying which color to use. Defaults to 'grn'.
> Accepts the following colors:
>     ['blk', 'blu', 'cyn', 'grn', 'mag', 'red', 'wht', 'yel']
>   1. _Type_: str
> 

> __Returns__: the modified string, including the ANSI/win32 color codes.
> _Return Type_: str

jaide.color_utils.**strip_color**(*search*):
>  Remove ANSI color codes from string.
> 

> __Purpose:__ Removes ANSI codes from a string. We use this to clean output
> from a jaide command before writing it to a file.
> 
> * __search__: The string to search through to remove any ANSI codes.
>   1. _Type_: str
> 

> __Returns__: The new string without any ANSI codes.
> _Return Type_: str

jaide.color_utils.**color_diffs**(*string*):
>  Add color ANSI codes for diff lines.
> 

> __Purpose:__ Adds the ANSI/win32 color coding for terminal output to output
> produced from difflib.
> 
> * __string__: The string to be replacing
>   1. _Type_: str
> 

> __Returns__: The new string with ANSI codes injected.
> _Return Type_: str

