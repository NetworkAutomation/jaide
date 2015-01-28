"""
This module is the Junos Aide/Jaide/JGUI project. It is free software for use
in manipulating junos devices. More information can be found at the github page
found here:      https://github.com/NetworkAutomation/jaide
"""
# This is for modifying printed output (used for --scp to rewrite the same line
# multiple times.) It is required to be at the top of the file.
from __future__ import print_function
try:
    from lxml import etree, objectify
    from ncclient import manager
    # needed to parse strings into xml for cases when ncclient doesn't handle
    # it (commit, validate, etc)
    import xml.etree.ElementTree as ET
    # RPCErrors are returned in certain instances, such as when the candidate
    # config is locked because someone is editing it.
    from ncclient.operations.rpc import RPCError
    from ncclient.operations.errors import TimeoutExpiredError
    from ncclient.transport import errors
    from os import path
    import paramiko
    import logging  # logging needed for disabling paramiko logging output
    import socket  # used for catching timeout errors on paramiko sessions
    import time
    from errors.errors import InvalidCommandError
except ImportError as e:
    print("FAILED TO IMPORT ONE OR MORE PACKAGES.\nNCCLIENT\thttps://github.com/leopoul/ncclient/\nPARAMIKO\thttps://github.com/paramiko/paramiko\n\n"
            "For windows users, you will also need PyCrypto:\nPYCRYPTO\thttp://www.voidspace.org.uk/python/modules.shtml#pycrypto"
            "\n\nNote that the --scp command also requires SCP:\n"
            "SCP\t\thttps://pypi.python.org/pypi/scp/0.8.0")
    print('\nScript Error:\n')
    raise e


# TODO: shell commands
# TODO: scp commands
# TODO: device status (health check)
# TODO: interface errors
class Jaide():
    def __init__(self, host, username, password, conn_timeout=5,
                 sess_timeout=300, conn_type="paramiko", port=22):
        """ Purpose: This is the initialization function for the Jaide class,
                   | which creates a connection to a junos device. It will
                   | return a Jaide object, which can then be used to actually
                   | send commands to the device. This function establishes the
                   | connection to the device via a NCClient manager object.

            @param host: The IP or hostname of the device to connect to.
            @type host: str
            @param username: The username for the connection
            @type username: str
            @param password: The password for the connection
            @type password: str
            @param conn_timeout: The timeout value, in seconds, for attempting
                               | to connect to the device.
            @type conn_timeout: int
            @param sess_timeout: The timeout value, in seconds, for the
                                  | session. If a command is sent and nothing
                                  | is heard back from the device in this
                                  | timeframe, the session is declared dead,
                                  | and times out.
            @type sess_timeout: int
            @param conn_type: The connection type that should be made. Several
                            | options are available: 'ncclient', 'scp', and
                            | 'paramiko', 'shell' and 'root'. 'paramiko' is
                            | used for operational commands, to allow for
                            | pipes. 'scp' is used for copying files to/from
                            | the device, and uses an SCP connection. 'shell'
                            | is for sending shell commands. 'root' is when the
                            | user is doing operational commands, but is logged
                            | in as root, (requires handling separately, since
                            | this puts the sessions into a shell prompt)
                            | 'ncclient' is used for all other commands.
            @type conn_type: str
            @param port: The destination port on the device to attempt the
                       | connection.
            @type port: int

            @returns: an instance of the Jaide class
            @rtype: object
        """
        # store object properties
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sess_timeout = sess_timeout
        self.conn_timeout = conn_timeout
        self._shell = ""
        self.conn_type = conn_type
        # make the connection to the device
        self.connect()

    def check_instance(function):
        """Purpose: This decorator function is used by all functions within
                  | the Jaide class that interact with a device to ensure the
                  | proper session type is in use. If it is not, it will
                  | attempt to migrate _session to that type before moving
                  | to the originally requested function.

            @param function: the function that is being wrapped around
            @type function: function

            @returns: the originally requested function
            @rtype: function
        """
        def wrapper(self, *args, **kwargs):
            func_trans = {
                "op_cmd": paramiko.client.SSHClient,
                "compare_config": manager.Manager,
                "commit_check": manager.Manager,
                "commit": manager.Manager,
                "shell_cmd": paramiko.client.SSHClient
            }
            # when doing an operational command, logging in as root
            # brings you to shell, so we need to enter the device as a shell
            # connection, and move to cli to perform the command
            # this is a one-off because the isinstance() check will be bypassed
            if self.username == "root" and function.__name__ == "op_cmd":
                if not self._shell:
                    self.conn_type = "root"
                    self.connect()
                # FIXME: if doing shell commands, then doing op cmds when logged in as root, the op cmds will fail because we're not moving to CLI here (no way to no if we're in shell or cli)
            # Have to call shell command separately, since we are using _shell
            # for comparison, not _session.
            elif function.__name__ == 'shell_cmd' and not self._shell:
                self.conn_type = "shell"
                self.connect()
            if isinstance(self._session, func_trans[function.__name__]):
                pass
            else:
                self.disconnect()
                if function.__name__ == "op_cmd":
                    self.conn_type = "paramiko"
                elif function.__name__ == "scp":
                    self.conn_type = "scp"
                else:
                    self.conn_type = "ncclient"
                self.connect()
            return function(self, *args, **kwargs)
        return wrapper

    def connect(self):
        """ Purpose: This method is used to make a connection to the junos
                   | device. The internal property conn_type is what
                   | determines the type of connection we make to the device.
                   | - 'paramiko' is used for operational commands (to allow
                   |            pipes in commands)
                   | - 'scp' is used for copying files
                   | - 'shell' is used for to send shell commands
                   | - 'root' is used when logging into the device as root, and
                   |            wanting to send operational commands
                   | - 'ncclient' is used for the rest (commit, compare_config,
                   |            commit_check)

            @returns: None
            @rtype: None
        """
        if self.conn_type == 'paramiko':
            self._session = paramiko.SSHClient()
            # These two lines set the paramiko logging to Critical to
            # remove extra messages from being sent to the user output.
            logger = logging.Logger.manager.getLogger(
                'paramiko.transport')
            logger.setLevel(logging.CRITICAL)
            self._session.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
            self._session.connect(hostname=self.host,
                                  username=self.username,
                                  password=self.password,
                                  port=self.port,
                                  timeout=self.conn_timeout)
        elif self.conn_type == "ncclient":
            self._session = manager.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.conn_timeout,
                device_params={'name': 'junos'},
                hostkey_verify=False
            )
            self._session.timeout = self.sess_timeout
        elif self.conn_type == 'scp':
            # todo: add in scp connection
            pass
        elif self.conn_type == 'shell':
            if not self._session:
                self.conn_type = 'paramiko'
                self.connect()
                self.conn_type = 'shell'
            if not self._shell:
                self._shell = self._session.invoke_shell()
                time.sleep(2)
            self._shell.send('start shell\n')
            time.sleep(2)
            self._shell.recv(9999)
        elif self.conn_type == 'root':
            # open the shell if necessary, and move it into CLI
            if not self._shell:
                self._shell = self._session.invoke_shell()
                time.sleep(2)
            self._shell.send("cli\n")
            time.sleep(4)
            self._shell.recv(9999)

    @check_instance
    def op_cmd(self, command, req_format='text', xpath_expr=""):
        """ Purpose: Used to send an operational mode command to the connected
                   | device. This requires and uses a paramiko.SSHClient() as
                   | the handler so that we can easily pass and allow all pipe
                   | commands to be used.
                   |
                   | We indiscriminately attach ' | no-more' on the end of
                   | every command so the device doesn't hold output. The
                   | req_format parameter can be set to 'xml' to force raw
                   | xml output in the reply.

            @param command: The single command that to retrieve output from the
                          | device. Any pipes will be taken into account.
            @type: str
            @param req_format: The desired format of the response, defaults to
                             | 'text', but also accepts 'xml'
            @type: str

            @returns: The reply from the device.
            @rtype: str
        """
        if not command:
            raise InvalidCommandError("Parameter 'command' cannot be empty")
        if req_format.lower() == 'xml' or xpath_expr:
            command += ' | display xml'
        command += ' | no-more\n'
        out = ''
        # when logging in as root, we are at shell, and need to move to cli to
        # run the command
        if self.username == 'root':
            self._shell.send(command)
            time.sleep(1)
            while self._shell.recv_ready():
                out += self._shell.recv(999999)
            # take off the command being sent and the prompt at the end.
            out = '\n'.join(out.split('\n')[1:-2])
        # not logging in as root, and can grab the output as normal.
        else:
            stdin, stdout, stderr = self._session.exec_command(command=command,
                                            timeout=float(self.sess_timeout))
            stdin.close()
            # read normal output
            while not stdout.channel.exit_status_ready():
                out += stdout.read()
            stdout.close()
            # read errors
            while not stderr.channel.exit_status_ready():
                out += stderr.read()
            stderr.close()
        return out if not xpath_expr else self.xpath(out, xpath_expr)

    @check_instance
    def shell_cmd(self, command=""):
        """ Purpose: Used to send a shell command to the connected device.
                   | This uses the self._shell instance, which should be a
                   | paramiko.Channel object, instead of a SSHClient.
                   | This is because we cannot send shell commands to the
                   | device using a SSHClient.

            @param command: The single command that to retrieve output from the
                          | device.
            @type: str

            @returns: The reply from the device.
            @rtype: str
        """
        if not command:
            raise InvalidCommandError("Parameter 'command' must not be empty.")
        command = command.strip() + '\n'
        self._shell.send(command)
        time.sleep(1)
        out = ''
        while self._shell.recv_ready():
            out += self._shell.recv(999999)
        # take off the command being sent and the prompt at the end.
        out = '\n'.join(out.split('\n')[1:-1])
        return out

    @check_instance
    def compare_config(self, commands="", req_format="text"):
        """ Purpose: This method will take in string of multiple commands,
                   | and perform and 'show | compare' on the device to show the
                   | differences between the active running configuration and
                   | the changes proposed by the passed commands parameter.

            @param commands: A string, filepath, or list of multiple commands
                           | that the device will compare with.
            @type: str or list
            @param req_format: The desired format of the response, defaults to
                             | 'text', but also accepts 'xml'
            @type: str

            @returns: The reply from the device.
            @rtype: str
        """
        if not commands:
            raise InvalidCommandError('No commands specified')
        clean_cmds = []
        for cmd in self.iter_cmds(commands):
            clean_cmds.append(cmd)
        self.lock()
        self._session.load_configuration(action='set', config=clean_cmds)
        out = self._session.compare_configuration()
        self.unlock()
        if req_format.lower() == "xml":
            return out
        return out.xpath(
            'configuration-information/configuration-output')[0].text

    @check_instance
    def commit_check(self, commands="", req_format="text"):
        """ Purpose: This method will take in string of multiple commands,
                   | and perform and 'commit check' on the device to ensure
                   | the commands are syntactically correct.

            @param commands: A string, filepath, or list of multiple commands
                           | that the device will compare with.
            @type: str or list
            @param req_format: The desired format of the response, defaults to
                             | 'text', but also accepts 'xml'
            @type: str

            @returns: The reply from the device.
            @rtype: str
        """
        if not commands:
            raise InvalidCommandError('No commands specified')
        clean_cmds = []
        for cmd in self.iter_cmds(commands):
            clean_cmds.append(cmd)
        self.lock()
        self._session.load_configuration(action='set', config=clean_cmds)
        # conn.validate() DOES NOT return a parse-able xml tree, so we
        # convert it to an ElementTree xml tree.
        results = ET.fromstring(self._session.validate(
            source='candidate').tostring)
        # release the candidate configuration
        self.unlock()
        if req_format == "xml":
            return ET.tostring(results)
        out = ""
        # we have to parse the elementTree object, and get the text
        # from the xml.
        for i in results.iter():
            # the success message is just a tag, so we need to get it
            # specifically.
            if i.tag == 'commit-check-success':
                out += 'configuration check succeeds\n'
            # this is for normal output with a tag and inner text, it will
            # strip the inner text and add it to the output.
            elif i.text is not None:
                if i.text.strip() + '\n' != '\n':
                    out += i.text.strip() + '\n'
            # this is for elements that don't have inner text, it will add the
            # tag to the output.
            elif i.text is None:
                if i.tag + '\n' != '\n':
                    out += i.tag + '\n'
        return out

    @check_instance
    def commit(self, commit_confirm=None, comment=None, at_time=None,
               synchronize=False, commands=""):
        """ Purpose: This method will take in string of multiple commands,
                   | and perform and 'commit check' on the device to ensure
                   | the commands are syntactically correct.

            @param commands: A string or list of multiple commands
                           | that the device will compare with.
                           | If a string, it can be a single command,
                           | multiple commands separated by commas, or
                           | a filepath location of a file with multiple
                           | commands, each on its own line.
            @type: str or list
            @param req_format: The desired format of the response, defaults to
                             | 'text', but also accepts 'xml'
            @type: str

            @returns: The reply from the device.
            @rtype: str
        """
        # ncclient doesn't support a truly blank commit, so if nothing is
        # passed, use 'annotate system' to make a blank commit
        if not commands:
            commands = "annotate system"
        commands = commands.split(',')
        # try to lock the candidate config so we can make changes.
        self._session.lock()
        self._session.load_configuration(action='set', config=commands)
        results = ""
        # commit_confirm and commit at are mutually exclusive. commit confirm
        # takes precedence.
        if commit_confirm:
            results = self._session.commit(confirmed=True,
                                           timeout=str(commit_confirm),
                                           comment=comment,
                                           synchronize=synchronize)
        else:
            results = self._session.commit(comment=comment, at_time=at_time,
                                           synchronize=synchronize)
        if results:
            # commit() DOES NOT return a parse-able xml tree, so we
            # convert it to an ElementTree xml tree.
            results = ET.fromstring(results.tostring)
            out = ''
            for i in results.iter():
                # the success message is just a tag, so we need to get it
                # specifically.
                if i.tag == 'commit-check-success':
                    out += 'configuration check succeeds\n'
                elif i.tag == 'commit-success':
                    out += 'commit complete\n'
                # this is for normal output with a tag and inner text, it will
                # strip the inner text and add it to the output.
                elif i.text is not None:
                    if i.text.strip() + '\n' != '\n':
                        out += i.text.strip() + '\n'
                # this is for elements that don't have inner text,
                # it will add the tag to the output.
                elif i.text is None:
                    if i.tag + '\n' != '\n':
                        out += i.tag + '\n'
            return out
        return False

    def disconnect(self):
        """ Purpose: Closes the current connection to the device, no matter
                   | what type it is.

            @returns: None
            @rtype: None
        """
        if self._shell:
            self._shell.close()
            self._shell = ""
        if isinstance(self._session, manager.Manager):
            self._session.close_session()
        elif isinstance(self._session, paramiko.client.SSHClient):
            self._session.close()
            self._session = ""
        # elif isinstance(self._session, scp_instnace):
        #     self._session.close_scp_instance()

    def lock(self):
        """ Purpose: Attempts to lock the session. Will only work if the
                   | session is of type 'ncclient', since that is the only
                   | time when you can lock the candidate configuration.
        """
        self._session.lock()

    def unlock(self):
        """ Purpose: Attempts to unlock the candidate configuration.
                   | self._session must of a ncclient connection for this
                   | to work.
        """
        self._session.unlock()

    @staticmethod
    def iter_cmds(commands):
        """ Purpose: This function is a generator that will read in either a
                   | plain text file of commands, a comma separated string
                   | of commands, or a list of commands, and will crop out any
                   | comments or blank lines, and yield individual commands.

            @param commands: This can be either a string that is a file
                           | location, a comma separated string of commands,
                           | or a python list of commands
            @type commands: str or list

            @returns: Yields each command in order
            @rtype: iterable of str
        """
        if isinstance(commands, basestring):
            # if the command argument is a filename, we need to open it.
            if path.isfile(commands):
                commands = open(commands, 'rb')
            # if the command string is a comma separated list, break it up.
            elif len(commands.split(',')) > 1:
                commands = commands.split(',')
        elif isinstance(commands, list):
            pass
        else:
            raise TypeError('commands parameter must be a \'str\' or \'list\'')
        for cmd in commands:
            # exclude commented lines, and skip blank lines (index error)
            try:
                if cmd.strip()[0] != "#":
                    yield cmd.strip()
            except IndexError:
                pass

    @staticmethod
    def xpath(source_xml, xpath_expr):
        """ Purpose: This function applies an Xpath expression to the XML
                   | supplied by source_xml. Returns a string subtree or
                   | subtrees that match the Xpath expression.

            @param source_xml: Plain text XML that will be filtered
            @type source_xml: str or lxml.etree.ElementTree.Element object
            @param xpath_expr: Xpath expression that we will filter the XML by.
            @type xpath_expr: str

            @returns: The filtered XML if filtering was successful. Otherwise,
                    | an empty string.
            @rtype: str
        """
        tree = source_xml
        if not isinstance(source_xml, ET.Element):
            tree = objectify.fromstring(source_xml)
        # clean up the namespace in the tags, as namespaces appear to confuse
        # xpath method
        for elem in tree.getiterator():
            # beware of factory functions such as Comment
            if isinstance(elem.tag, basestring):
                i = elem.tag.find('}')
                if i >= 0:
                    elem.tag = elem.tag[i+1:]

        # remove unused namespaces
        objectify.deannotate(tree, cleanup_namespaces=True)
        filtered_list = tree.xpath(xpath_expr)
        # Return string from the list of Elements
        matches = ''.join(etree.tostring(
            element, pretty_print=True) for element in filtered_list)
        return matches if matches else ""

    @property
    def host(self):
        return self.host

    @host.setter
    def host(self, value):
        self.host = value

    @property
    def conn_type(self):
        return self.conn_type

    @conn_type.setter
    def conn_type(self, value):
        self.conn_type = value

    @property
    def username(self):
        return self.username

    @username.setter
    def username(self, value):
        self.username = value

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, value):
        self.password = value

    @property
    def port(self):
        return self.port

    @port.setter
    def port(self, value):
        self.port = value

    @property
    def conn_timeout(self):
        return self.conn_timeout

    @conn_timeout.setter
    def conn_timeout(self, value):
        self.conn_timeout = value

    @property
    def sess_timeout(self):
        return self.sess_timeout

    @sess_timeout.setter
    def sess_timeout(self, value):
        self.sess_timeout = value
        self._session.timeout = value

def do_netconf(ip, username, password, function, args, write_to_file, timeout=300):
    """ Purpose: To open an NCClient manager session to the device, and run the appropriate function against the device.

        @param ip: String of the IP of the device, to open the connection, and for logging purposes.
        @type ip: str or unicode
        @param username: The string username used to connect to the device.
        @type useranme: str or unicode
        @param password: The string password used to connect to the device.
        @type password: str or unicode
        @param function: Pointer to function to run after opening connection
        @type function: function
        @param args: Args to pass through to function
        @type args: list
        @param write_to_file: The filepath specified by the user as to where to place the output from the script. Used to prepend the output
                            | string with the filepath, so that the write_output() function can find it easily, without needing another argument.
        @type write_to_file: str or unicode
        @param timeout: Sets netconf timeout. Defaults to 300 seconds. A higher value may be desired for long running commands,
                      | such as 'request system snapshot slice alternate'
        @type timeout: int

        @returns: The string output that should displayed to the user, which eventually makes it to the write_output() function.
        @rtype: str
    """
    user_output = ""
    if write_to_file:  # this is used to track the filepath that we will output to. The write_output() function will pick this up.
        user_output += "*****WRITE_TO_FILE*****" + write_to_file[1] + "*****WRITE_TO_FILE*****" + write_to_file[0] + "*****WRITE_TO_FILE*****"
    try:
        # Uses paramiko for show commands to allow pipe modifiers, and allow to move between shell and operational mode
        # depending on the user we log into the device as.
        if function == multi_cmd:
            ssh = paramiko.SSHClient()
            # These two lines set the paramiko logging to Critical to remove messages from being sent to the user output.
            logger = logging.Logger.manager.getLogger('paramiko.transport')
            logger.setLevel(logging.CRITICAL)
            # automatically add the device host key if not already known.
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # make the connection to the device.
            ssh.connect(hostname=ip, username=username, password=password, timeout=5)
            conn = ssh  # need to copy the connection pointer in case we have to move in/out of shell, based on the user they logged in with.
            if args[1]:  # we are sending shell commands
                # shell commands require an invoke_shell() to maintain continuous session context for the commands.
                try:
                    conn = conn.invoke_shell()
                except paramiko.SSHException as e:
                    user_output += '=' * 50 + '\nAuthenticated to the device %s, but failed to open connection a paramiko shell.\nParamiko exception: %s' % (ip, str(e))
                    return user_output
                else:
                    time.sleep(1)
                    conn.send('start shell\n')
                    time.sleep(1.5)
                    conn.recv(9999)
            else:  # we are sending operational mode commands.
                if username == "root":
                    # If user is root, we use paramiko.Channel to allow us to move from shell to cli
                    # run_cmd has logic to detect if it's passed a paramiko.SSHClient object or a paramiko.Channel
                    # and handle accordingly
                    try:
                        conn = conn.invoke_shell()
                    except paramiko.SSHException as e:
                        user_output += '=' * 50 + '\nAuthenticated to the device %s, but failed to open connection a paramiko shell.\nParamiko exception: %s' % (ip, str(e))
                        return user_output
                    else:
                        conn.send("cli\n")
                        # Moving from shell to CLI can take a few seconds, so wait
                        time.sleep(4)
                        # Moving from shell to CLI outputs a bunch of garbage which writes over itself
                        # so we grab it here and discard it
                        conn.recv(9999)
        else:  # open a netconf connection to the device using NCClient manager class
            conn = manager.connect(
                host=ip,
                port=22,
                username=username,
                password=password,
                timeout=5,
                device_params={'name':'junos'},
                hostkey_verify=False
                )
            conn.timeout = timeout  # Set the timeout value, based on what they entered, or 300 for the default.
    except errors.SSHError:
        user_output += '=' * 50 + '\nUnable to connect to port 22 on device: %s\n' % ip
    except errors.AuthenticationError:  # NCClient auth failure
        user_output += '=' * 50 + '\nAuthentication failure for device: %s\n' % ip
    except paramiko.AuthenticationException:  # Paramiko auth failure
        user_output += '=' * 50 + '\nAuthentication failure for device: %s\n' % ip
    except paramiko.SSHException as e:
        user_output += '=' * 50 + '\nError connecting to device: %s\nError: %s' % (ip, str(e))
    except socket.timeout:
        user_output += '=' * 50 + '\nTimeout exceeded connecting to device: %s\n' % ip
    else:
        # if there are no args to pass through
        if args is None:
            user_output += function(conn, ip)
        # if we do have args to pass through
        else:
            user_output += function(conn, ip, *args)
    # no matter what happens, return the output
    return user_output


# need a global variable for the filename at module scope to allow for the callback function copy_status() to 
# be able to test if the filename has changed for the file that is being copied. If it has, the output is 
# moved down a line, so you can easily see all the filenames being copied. 
gbl_filename = ''
# FIXME: when a file fails to copy, it stops the rest of the transfer. Perhaps a way to skip that file?  --Engaged the SCP module github repo, awaiting response. 
def copy_status(filename, size, sent):
    """ Purpose: This is the callback function for --scp, when we copying to/from a single device (and therefore not multiprocessing),
               | it will update the user to the status of the current file being transferred. 

        @param filename: The filename of the file that is currently being copied. 
        @type filename: str or unicode
        @param size: The total size of the file that is currently being copied in bytes. 
        @type size: int
        @param sent: The number of bytes of the current file that have already been transferred.
        @type sent: int

        @returns: None
    """
    global gbl_filename  # Grab the global variable for the filename being transferred. 
    # does the logic to get an accurate percentage of the amount sent of the current file.
    output = "Transferred %.0f%% of the file %s" % ((float(sent) / float(size) * 100), filename)
    # appends whitespace to the end of the string up to the 120th column, so that the output doesn't look garbled from previous output. 
    output += (' ' * (120 - len(output)))
    # If the filename has changed, move to the next line and update the filename. 
    if filename != gbl_filename:
        print('')
        gbl_filename = filename
    # prints the output, end='\r' ends lines with a carriage return instead of new line, 
    # so that the output constantly rewrites the same line (for the current file). This line is what requires the import
    # for 'from __future__ import print_function' 
    print(output, end='\r')


def copy_file(scp_source, scp_dest, ip, username, password, direction, write, multi=False, callback=copy_status):
    """ Purpose: This is the function to scp a file to/from the specified source and destinations

        @param scp_source: source file for the SCP transaction
        @type scp_source: str
        @param scp_dest: destination file for the SCP transaction
        @type scp_dest: str
        @param ip: the remote IP address for the SCP transaction
        @type ip: str
        @param username: the username for the remote device.
        @type username: str
        @param password: the password for the remote device.
        @type password: str
        @param direction: the direction of the copy operation, either push or pull.
        @type direction: str
        @param write: The copy_file function is unique in that since it uses callback, it needs to be aware
                    | if we are outputting to a file later. If we are, then suppress certain output. If we
                    | aren't writing to a file, this function will print updates immediately, and return an 
                    | empty string to write_output(), since we've already printed everything to the user. 
                    | This write variable is the string of the filepath where the output should be written. 
        @type write: str
        @param multi: Flag should be set to true when sending to multiple devices. This is used to determine 
                    | the naming scheme of the destination files. 
        @type multi: boolean
        @param callback: definition of callback function to be used by Paramiko for status updates. This is only
                       | used when scp'ing to/from a single device, and generally should be passed None otherwise.
        @type callback: function 

        @returns: The string output to be shown to the user, containing the information of what happened 
                | during the copy. 
        @rtype: str
    """
    try: 
        # scp is also imported.
        from scp import SCPClient, SCPException
    except ImportError as e:
        print('Failed to import PARAMIKO or SCP packages, which are needed for the --scp command. They can be found at:\n'
               'PARAMIKO\thttps://github.com/paramiko/paramiko\nSCP\t\thttps://pypi.python.org/pypi/scp/0.8.0')
        print('\nScript Error:\n')
        raise e
    # First we open a paramiko ssh session, then open an scp session using the paramiko as transport.
    ssh = paramiko.SSHClient()
    # These two lines remove paramiko logging output from being seen. 
    logger = logging.Logger.manager.getLogger('paramiko.transport')
    logger.setLevel(logging.CRITICAL)
    # This will automatically add the remote host key if it is the first time connecting to the device.
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    screen_output = ''
    if isinstance(write, list):
        screen_output += "*****WRITE_TO_FILE*****" + write[1] + "*****WRITE_TO_FILE*****" + write[0] + "*****WRITE_TO_FILE*****"
    # If callback is something other than None, we are running against one device, and will be printing status output.
    # So we must add a leading \n to move below the callback output. 
    if callback != None:  
        screen_output += '\n'
    # This will make the connection and handle errors Authentication or rejection errors. 
    screen_output += ('=' * 50 + '\nResults from device: %s\n' % ip)
    try:
        ssh.connect(ip, port=22, username=username, password=password, timeout=10)
    except paramiko.AuthenticationException:
        return screen_output + '!!! Authentication failed for device %s. !!!\n' % ip
    except socket.timeout:
        return screen_output + '!!! Connection to device %s timed out. !!!\n' % ip
    except socket.error:
        return screen_output + '!!! Connection to device %s on port 22 was refused. !!!\n' % ip
    else:
        # create the SCPClient session using the paramiko ssh session as a transport channel.
        scp = SCPClient(ssh.get_transport(), progress=callback)

        # source and destination filepath validation and cleanup. 
        if scp_dest[-1] != '/':  # Check if the destination ends in a '/', if not, we need to add it. 
            scp_dest += '/'
        # If the source ends in a slash, we need to remove it. For copying directories, this will ensure that the local
        # directory gets created remotely, and not just the contents.
        # Basically, this forces the behavior 'scp -r /var/log /dest/loc' instead of 'scp -r /var/log/* /dest/loc'
        if scp_source[-1] == '/':
            scp_source = scp_source[:-1]
        # escape any spaces in the file paths. 
        scp_source = scp_source.replace(' ', '\\ ')
        scp_dest = scp_dest.replace(' ', '\\ ')
        source_file = scp_source.split('/')[-1]  # grab just the filename, or the last folder in the tree if the source is a directory.
        # Create the output variables.
        temp_output = ''
        if direction.lower() == 'pull':  # if we're pulling files, perform the proper scp.get() request
            if multi:  # If we're grabbing from multiple devices, we need to append the ip to the destination file/folder. 
                destination_file = scp_dest + ip + '_' + source_file
            else:
                destination_file = scp_dest + source_file
            screen_output += ('Retrieving %s:%s, and putting it in %s\n' % (ip, scp_source, destination_file))
            destination_file = destination_file.replace(' ', '\\ ')  # escape the spaces in the destination filepath.
            try:
                scp.get(scp_source, destination_file, recursive=True, preserve_times=True)
            except SCPException as e:  # The get or push operation failed, so let the user know
                return screen_output + '!!! Error during copy from ' + ip + '. Some files may have failed to transfer. SCP Module error:\n' + str(e) + '\n!!!\n'
            except (IOError, OSError) as e:  # IOError is received for a local filepath malfunction
                return screen_output + '!!! The local filepath was not found! Note that \'~\' cannot be used. Error: ' + str(e) + ' !!!\n'
            except KeyboardInterrupt:
                return screen_output + '!!! Received KeyboardInterrupt, SCP operation halted !!!\n'
            else:
                temp_output += 'Received %s from %s.\n' % (scp_source, ip)
        elif direction.lower() == 'push': # perform an scp.put() for pushing files.
            screen_output += ('Pushing %s to %s:%s\n' % (scp_source, ip, scp_dest))
            try:
                scp.put(scp_source, scp_dest, recursive=True, preserve_times=True)
            except SCPException as e:  # The get or push operation failed, so let the user know
                return screen_output + '!!! Error during copy to ' + ip + '. Some files may have failed to transfer. SCP Module error:\n' + str(e) + '\n!!!\n'
            except (IOError, OSError) as e:  # IOError is received for a local filepath malfunction
                return screen_output + '!!! The local filepath was not found! Note that \'~\' cannot be used. Error: ' + str(e) + ' !!!\n'
            except KeyboardInterrupt:
                return screen_output + '!!! Received KeyboardInterrupt, SCP operation halted !!!\n'
            else:
                temp_output += 'Pushed %s to %s:%s\n' % (scp_source, ip, scp_dest)
        screen_output += temp_output
        return screen_output


def dev_info(conn, ip):
    """ Purpose: This is the function called by using the --info flag on the command line.
               | It grabs the hostname, model, running version, and serial number of the device.

        @param conn: This is the ncclient manager connection to the remote device.
        @type conn: ncclient.manager.Manager
        @param ip: String containing the IP of the remote device, used for logging purposes.
        @type ip: str

        @returns: The output that should be shown to the user.
        @rtype: str
    """
    # get hostname, model, and version from 'show version'
    software_info = conn.get_software_information(format='xml')
    host_name = software_info.xpath('//software-information/host-name')[0].text
    model = software_info.xpath('//software-information/product-model')[0].text
    version = (software_info.xpath('//software-information/package-information/comment')[0].text.split('[')[1].split(']')[0])
    # get serial number from 'show chassis hardware'
    show_chass_hardware = conn.get_chassis_inventory(format='xml')
    # If we're hitting an EX, grab each Routing Engine Serial number, to get all RE SNs in a VC
    if ('EX' or 'ex' or 'Ex') in show_chass_hardware.xpath('//chassis-inventory/chassis/chassis-module/description')[0].text:
        serial_number = ""
        for module in show_chass_hardware.xpath('//chassis-inventory/chassis/chassis-module'):
            if 'Routing Engine' in module.xpath('name')[0].text:
                serial_number += module.xpath('name')[0].text + ' Serial #: ' + module.xpath('serial-number')[0].text + "\n"
    else:  # Any other device type, just grab chassis SN
        serial_number = 'Chassis Serial Number: ' + show_chass_hardware.xpath('//chassis-inventory/chassis/serial-number')[0].text
    conn.close_session()
    return '=' * 50 + '\nResults from device: %s\n\nHostname: %s \nIP: %s \nModel: %s \nJunos: %s \n%s\n' % (ip, host_name, ip, model, version, serial_number)


def health_check(conn, ip):
    """ Purpose: This is the function called by using the --health flag on the command line.
               | It grabs the cpu/mem usage, system/chassis alarms, top 5 processes, if the primary/backup partitions are on different versions.

        @param conn: This is the ncclient manager connection to the remote device.
        @type conn: ncclient.manager.Manager
        @param ip: String containing the IP of the remote device, used for logging purposes.
        @type ip: str

        @returns: The output that should be shown to the user.
        @rtype: str
    """
    output = '=' * 50 + '\nResults from device: %s\n\nChassis Alarms: \n' % ip
    # Grab chassis alarms, system alarms, show chassis routing-engine, 'show system processes extensive', and also xpath to the relevant nodes on each. 
    chassis_alarms = conn.command(command="show chassis alarms", format='xml').xpath('//alarm-detail')
    system_alarms = conn.command(command="show system alarms", format='xml').xpath('//alarm-detail')
    re_info = conn.command(command="show chassis routing-engine", format='xml').xpath('//route-engine')
    proc = conn.command(command="show system processes extensive", format='xml').xpath('output')[0].text.split('\n')
    if chassis_alarms == []:  # Chassis Alarms
        output += '\tNo chassis alarms active.\n'
    else: 
        for i in chassis_alarms:
            output += '\t' + i.xpath('alarm-class')[0].text.strip() + ' Alarm \t'
            output += '\t' + i.xpath('alarm-time')[0].text.strip() + '\n'
            output += '\t' + i.xpath('alarm-description')[0].text.strip() + '\n'
    output += '\nSystem Alarms: \n'
    if system_alarms == []:  # System Alarms
        output += '\tNo system alarms active.\n'
    else: 
        for i in system_alarms:
            output += '\t' + i.xpath('alarm-class')[0].text.strip() + ' Alarm \t'
            output += '\t' + i.xpath('alarm-time')[0].text.strip() + '\n'
            output += '\t' + i.xpath('alarm-description')[0].text.strip() + '\n'
    output += '\nRouting Engine Information:'
    if re_info == []:  # RE information
        output += '\nNo Routing Engines found...\n'
    else:
        for i in re_info:  # loop through all REs for info.
            if i.xpath('slot') != []:  # for multi-RE chassis systems, print slot and mastership status. 
                output += '\nRE' + i.xpath('slot')[0].text + ' Status: \t' + i.xpath('status')[0].text + '\n'
                output += '\tMastership: \t' + i.xpath('mastership-state')[0].text
            if i.xpath('memory-buffer-utilization') != []:  # EX/MX response tags
                output += '\n\tUsed Memory %: \t' + i.xpath('memory-buffer-utilization')[0].text + '\n'
                output += '\tCPU Temp: \t' + i.xpath('cpu-temperature')[0].text + '\n'
            if i.xpath('memory-system-total-util') != []:  # SRX response tags
                output += '\n\tUsed Memory %: \t' + i.xpath('memory-system-total-util')[0].text + '\n'                
                output += '\tCPU Temp: \t' + i.xpath('temperature')[0].text + '\n'
            output += '\tIdle CPU%: \t' + i.xpath('cpu-idle')[0].text + '\n'
            if i.xpath('serial-number') != []:  # serial number not shown on single RE MX chassis. 
                output += '\tSerial Number: \t' + i.xpath('serial-number')[0].text + '\n'
            output += '\tLast Reboot: \t' + i.xpath('last-reboot-reason')[0].text + '\n'
            output += '\tUptime: \t' + i.xpath('up-time')[0].text + '\n'
    output += '\nTop 5 busiest processes:\n'
    for line_number in range(8, 14):  # Grabs the top 5 processes and the header line. 
        output += proc[line_number] + '\n'
    conn.close_session()
    return output


def int_errors(conn, ip):
    """ Purpose: This function is called for the -e flag. It will let the user know if there are any interfaces with errors, and what those interfaces are.

        @param conn: This is the ncclient manager connection to the remote device.
        @type conn: ncclient.manager.Manager
        @param ip: String containing the IP of the remote device, used for logging purposes.
        @type ip: str

        @returns: The output that should be shown to the user.
        @rtype: str
    """
    output = []  # used to store the list of interfaces with errors.
    error_counter = 0  # used to count the number of errors found on a device.
    output.append('=' * 50 + '\nResults from device: %s' % ip)  # append a header row to the output.
    # strip down to a list of each interface element in the xml tree
    int_xml = conn.command(command='show interfaces extensive', format='xml')
    interfaces = int_xml.xpath('//physical-interface')
    interfaces += int_xml.xpath('//logical-interface')
    for i in interfaces:
        int_name = i.xpath('name')[0].text.strip()  # Grab the interface name for user output. 
        # Only check certain interface types. 
        if ('ge' or 'fe' or 'ae' or 'xe' or 'so' or 'et' or 'vlan' or 'lo0' or 'irb') in int_name:
            try:  # make sure the interface has an operational status to retrieve, otherwise skip the interface. 
                op_status = i.xpath('oper-status')[0].text
            except IndexError:
                pass
            else:
                if 'up' in op_status:
                    error_list = {}
                    # Grab the input errors
                    try:
                        in_err = i.xpath('input-error-list')[0]
                    except IndexError:
                        pass
                    else:
                        # Loop through all subelements of input-error-list, storing them in a dictionary of { 'tag' : 'value' } pairs.
                        for x in range(len(in_err)):
                            error_list[in_err[x].tag] = int(in_err[x].text.strip())
                    # Grab the output errors
                    try:
                        out_err = i.xpath('output-error-list')[0]
                    except IndexError:
                        pass
                    else:
                        for x in range(len(out_err)):
                            error_list[out_err[x].tag] = int(out_err[x].text.strip())

                    # Loop through and check for errors
                    # key is the xml tag name for the errors. value is the integer for that counter.
                    for key, value in error_list.iteritems():
                        if key == 'carrier-transitions':
                            if value > 50:
                                output.append("%s has greater than 50 flaps" % int_name)
                                error_counter += 1
                        elif value > 0:
                            output.append("%s has %s of %s." % (int_name, value, key))
                            error_counter += 1
    if error_counter == 0:
        output.append('No interface errors were detected on this device.\n')
    else:  # if there were errors, we need to append a blank line for separation from the next device. 
        output.append('')
    return '\n'.join(output)


def make_commit(conn, ip, commands, commit_check, commit_confirm, commit_blank, comment, at_time, synchronize):
    """ Purpose: This function will send set command(s) to a device, and commit the change. It can be called by any function that 
               | needs to commit, currently used by the -s flag. The commit can be modified to be just a commit check 
               | with the --check flag, and commit confirm with the --confirm flag. It takes a single string for one set command, or a list of 
               | strings for multiple commands to be committed. 

        @param conn: This is the ncclient manager connection to the remote device.
        @type conn: ncclient.manager.Manager
        @param ip: String containing the IP of the remote device, used for logging purposes.
        @type ip: str
        @param commands: String containing the set command to be sent to the device, or a list of strings of multiple set commands.
                       | Either way, the function will respond accordingly, and only one commit will take place.
        @type commands: str
        @param commit_check: A bool set to true if the user wants to only run a commit check, and not commit any changes.
        @type commit_check: bool
        @param commit_confirm: An int of minutes that the user wants to commit confirm for.
        @type commit_confirm: int
        @param commit_blank: A bool set to true if the user wants to only make a blank commit.
        @type commit_blank: bool
        @param comment: A string that will be logged to the commit log describing the commit.
        @type comment: str
        @param at_time: A string containing the time or time and date of when the commit should happen. Junos is expecting
                      | one of two formats:
                      | A time value of the form hh:mm[:ss] (hours, minutes, and optionally seconds)
                      | A date and time value of the form yyyy-mm-dd hh:mm[:ss] (year, month, date, hours, minutes, and optionally seconds)
        @type at_time: str
        @param synchronize: A bool set to true if the user wants to synchronize the commit across both REs.
        @type synchronize: bool

        @returns: The output that should be shown to the user.
        @rtype: str
    """
    screen_output = '=' * 50 + '\nResults from device: %s\n' % ip
    # we're making a blank commit, and need a one liner that won't do anything, since netconf doesn't support just making a blank commit
    if commit_blank:  
        commands = "annotate system"
    elif isinstance(commands, basestring): # if command is a string, otherwise will cause error with isfile
        if path.isfile(commands):  # if the command argument is a filename, we need to open it. 
            try:
                commandsfile = open(commands, 'rb')  # open the command list in read only mode, the 'b' is for windows compatibility.
            except IOError as e:
                screen_output += ('Couldn\'t open the command list file %s due to the error:\n%s' % (commands, str(e)))
                return screen_output
            else:
                commands = ""
                for line in commandsfile:
                    try:
                        if line[0] != "#":  # skip comments in a set list file. 
                            commands += line.strip() + '\n'
                    except IndexError:  # blank lines in a set list file will return an Index Error. 
                        pass
        elif len(commands.split(',')) > 1:  # if the command string is a comma separated list, break it up. 
            commands = commands.split(',')
    try:
        conn.lock()  # try to lock the candidate config so only the script can make changes.
        conn.load_configuration(action='set', config=commands)
    # RPC error is received when the configuration database is changed, meaning someone is actively editing the config.
    except RPCError:
        screen_output += "\nUncommitted changes left on the device or someone else is in edit mode, couldn't lock the candidate configuration. Backing out...\n"
    else:
        if commit_check:  # If they just want to validate the config, without committing
            try:
                # conn.validate() DOES NOT return a parse-able xml tree, so we convert it to an ElementTree xml tree.
                results = ET.fromstring(conn.validate(source='candidate').tostring)
            except:
                screen_output += "Failed to commit check on device %s for an unknown reason." % ip
            else:
                # add the 'show | compare' output.
                compare_config = conn.compare_configuration()
                screen_output += "Comparison results:\n" + compare_config.xpath('configuration-information/configuration-output')[0].text + '\n'
                screen_output += "\nCommit check results from: %s\n" % ip  # prep the output with a header line
                for i in results.iter():  # loop over the results
                    if i.tag == 'commit-check-success':  # print the successful message if we see the right tag, since it isn't stored in XML
                        screen_output += 'configuration check succeeds\n'
                    elif i.text != None:  # this is for normal output with a tag and inner text, it will strip the inner text and add it.
                        if i.text.strip() + '\n' != '\n':
                            screen_output += i.text.strip() + '\n'
                    elif i.text == None:  # this is for tags that don't have inner text, it will add the tag to the output.
                        if i.tag + '\n' != '\n':
                            screen_output += i.tag + '\n'
        else:
            # add the 'show | compare' output.
            compare_config = conn.compare_configuration()
            screen_output += "Comparison results:\n" + compare_config.xpath('configuration-information/configuration-output')[0].text + '\n'
            results = ""
            if commit_confirm:
                screen_output += "Attempting to commit confirm on device: %s\n" % ip
                try:
                    results = conn.commit(confirmed=True, timeout=str(commit_confirm), comment=comment, synchronize=synchronize)
                except RPCError as e:
                    screen_output += 'Commit could not be completed on this device, due to the following error: \n' + str(e)
            else:  # If they didn't want commit confirm, just straight commit dat shit.
                screen_output += "Attempting to commit on device: %s\n" % ip
                try:
                    results = conn.commit(comment=comment, at_time=at_time, synchronize=synchronize)
                except RPCError as e:
                    screen_output += 'Commit could not be completed on this device, due to the following error: \n' + str(e)
            # conn.commit() DOES NOT return a parse-able xml tree, so we convert it to an ElementTree xml tree.
            if results:
                results = ET.fromstring(results.tostring)
                # This check is for if the commit was successful or not, and update the user accordingly.
                if results.find('commit-check-success') is None:  # None is returned for elements found without a subelement, as in this case.
                    if commit_confirm:
                        screen_output += 'Commit complete on device: %s. It will be automatically rolled back in %s minutes, unless you commit again.\n' % (ip, str(commit_confirm))
                    elif at_time: 
                        screen_output += 'Commit staged to happen at %s on device: %s' % (at_time, ip) 
                    else:
                        screen_output += 'Commit complete on device: %s\n' % ip
                else:
                    screen_output += 'Commit failed on device: %s with the following errors:\n' % ip
                    # for each line in the resultant xml, iterate over and print out the non-empty lines.
                    for i in results.findall('commit-results')[0].itertext():
                        if i.strip() != '':
                            screen_output += '\n' + i.strip()
    # except:  # catchall error for any other unforeseen events.
        # screen_output = '=' * 50 + '\nCommit failed on device: %s for an unknown reason.' % ip
    try:
        conn.unlock()
        conn.close_session()
    # RPC error is received when the configuration database is changed, meaning someone is actively editing the config. 
    # We've already let the user know, so just need to pass.
    except RPCError:
        pass
    except TimeoutExpiredError:
        screen_output += '!!! Timed out trying to unlock the configuration. Check device state manually.\n'
    return screen_output


def xpath_filter(router_output, xpath_expr):
    """ Purpose: This function applies an Xpath expression to the XML returned by the network element. The function
                 returns a string subtree or subtrees that match the Xpath expression.

        @param router_output: Plain text XML, which is the response from the device that we are filtering.
        @type router_output: str
        @param xpath_expr: Xpath expression, the rules that we will filter the XML on.
        @type xpath_expr: str

        @returns: The filtered XML if filtering was successful. Otherwise, a string explaining nothing matched the filter.
        @rtype: str
    """
    tree = objectify.fromstring(router_output)

    # check for valid Xpath
    try:
        tree.xpath(xpath_expr)
    except etree.XPathEvalError, xpath_exception:
        return "Invalid XPath '{}': {}".format(xpath_expr, xpath_exception)

    # clean up the namespace in the tags, as namespaces appear to confuse xpath method
    for elem in tree.getiterator():
        if isinstance(elem.tag, basestring): # beware of factory functions such as Comment
            i = elem.tag.find('}')
            if i >= 0:
                elem.tag = elem.tag[i+1:]

    # remove unused namespaces
    objectify.deannotate(tree, cleanup_namespaces=True)

    filtered_tree_list = tree.xpath(xpath_expr)

    # Return string from the list of Elements or warning message
    return_string = ''.join(etree.tostring(element, pretty_print=True) for element in filtered_tree_list)
    return return_string if return_string else "No matching nodes for Xpath expression."


def multi_cmd(conn, ip, commands, shell, format='text', timeout=300):
    """ Purpose: This function will determine if we are trying to send multiple commands to a device. It is used when the 
               | -c flag is used. If we have more than one command to get output for, then we need to split up the commands
               | and run them individually. Otherwise, we just send the one command. No matter how they sent the command(s)
               | to us (list, filepath, or single command), we take that information and turn it into a list of command(s).
               | We then loop over the list, running run_cmd() for each one. 

        @param conn: the connection to the remote device, using one of two paramiko sub classes. 
        @type conn: paramiko.Channel
        @param ip: String containing the IP of the remote device, used for logging purposes.
        @type ip: str
        @param commands: String containing one of three things: 
                       | A single operational show command.
                       | A comma separated list of show commands.
                       | A filepath pointing to a file with a show command on each line. 
        @type commands: str
        @param shell: boolean stating whether or not we are sending shell commands.
        @type shell: bool
        @param timeout: integer in seconds for the timeout we should expect for each command we send. Defaults to 300 seconds.
        @type timeout: int

        @returns: The output that should be shown to the user.
        @rtype: str
    """
    screen_output = '=' * 50 + '\nResults from device: %s' % ip
    # Each case of this if statement is just to get the command(s) into a list of strings for each command
    if path.isfile(commands):  # if the user gave us a filepath of multiple commands
        try:
            commands = open(commands, 'rb')
        except IOError as e:
            screen_output = ('Couldn\'t open the command list file %s due to the error:\n' % commands)
            raise e
    elif len(commands.split(',')) > 1:  # if the user gave us a comma separated list. 
        commands = commands.split(',')
    else:  # all else fails, they gave us just one command
        temp_cmd = commands
        commands = []
        commands.append(temp_cmd)
    for cmd in commands:  # iterate over the list
        # Only run the command if it's not a blank line or a comment. 
        if cmd.strip() != "" and cmd.strip()[0] != "#":
            xpath_expr = ''
            if shell: # make sure shell commands end in '\n', so the command will actually send.
                cmd = cmd.strip() + "\n"
            # adding ' | no-more' ensures operational commands don't hold output
            else:
                # get xpath expression from line in file if it exists
                # if there is an xpath expr, the output will be xml,
                # overriding the format parameter
                #
                # Example line in file: show route % //rt-entry
                if len(cmd.split('%')) == 2:
                    op_cmd = cmd.split('%')[0]
                    xpath_expr = cmd.split('%')[1].strip()
                    op_cmd = op_cmd.strip() + " | display xml | no-more\n"
                    # print(op_cmd)
                elif format == 'xml':
                    cmd = cmd.strip() + " | display xml | no-more\n"
                else:
                    cmd = cmd.strip() + " | no-more\n"
            if xpath_expr:
                screen_output += '\n> ' + op_cmd.strip() + ' % ' + xpath_expr + '\n' + xpath_filter(run_cmd(conn, ip, op_cmd,
                                 timeout).strip(), xpath_expr) + '\n' 
            else:
                screen_output += '\n> ' + cmd + run_cmd(conn, ip, cmd, timeout)
    try:
        conn.close_session()
    except AttributeError:
        try:
            conn.close()
        except:
            pass
    return screen_output


def run_cmd(conn, ip, command, timeout=300):
    """ Purpose: For the -c flag, this function is called. It will connect to a device, run the single specified command, 
               | and return the output. There is logic to see if the connection we are receiving is a type of 
               | paramiko.Channel. If so, we logged in as root, and had to get to the CLI first, meaning we execute the 
               | command using send() rather than exec_command(). Unfortunately, exec_command() couldn't handle getting 
               | into CLI, so we needed a method for handling if the user is logging in as root and reaching shell first.

        @param conn: the connection to the remote device, using one of two paramiko sub classes. 
        @type conn: paramiko.Channel
        @param ip: String containing the IP of the remote device, used for logging purposes.
        @type ip: str
        @param command: String containing the command to be sent to the device.
        @type command: str
        @param timeout: integer timeout value for the session, in seconds.
        @type command: int

        @returns: The output that should be shown to the user.
        @rtype: str
    """
    output = ""
    # check what type the connection is so we know if we logged in as root or not, and how we need to send the command and get output. 
    # if we are using a paramiko.Channel we have to send the command and then wait because we had to use a persistent session to move
    # the user from one op mode to another (ie shell to cli or vice versa)
    if isinstance(conn, paramiko.Channel):
        conn_output = ""
        try:
            conn.send(command)
            time.sleep(2)
            # recv_ready() returns True if there is buffered data
            # we wait after reading to make sure the device isn't putting more data to buffer
            # 3/4 seconds seems enough, but may still cause issues on long-running commands
            while conn.recv_ready():
                conn_output += conn.recv(999999)
                time.sleep(.75)
        except Exception as e:
            output += '\nError occurred on %s:\n%s\n' % (ip, str(e))
        else:
            try:
                # First substring removes the output showing us sending the command, the second
                # removes the new prompt received at the end.
                temp_out = conn_output.split("\n")[1:-1]
            except IndexError:
                output += conn_output
            else:
                try:
                    if temp_out[-1][0] == '{':  # the third one removes the banner message, if it exists. (On VC's for example.)
                        temp_out = temp_out[0:-1]
                except IndexError: 
                    pass
                finally:
                    output += "\n" + "\n".join(temp_out) + "\n"
    # If we are not using a paramiko.Channel connection object (ie; not logged in as root for op command),
    # we can use exec_command which is easier & quicker because we don't have to catch output from the buffer manually.
    elif isinstance(conn, paramiko.client.SSHClient):
        try:
            stdin, stdout, stderr = conn.exec_command(command=command, timeout=float(timeout))
            stdin.close()
            # add a newline to separate the output 
            output += "\n"
            # channel.exit_status_ready returns false until the command has completed executing
            while not stdout.channel.exit_status_ready():
                output += stdout.read()
            stdout.close()
            while not stderr.channel.exit_status_ready():
                output += stderr.read()
            stderr.close()
        except paramiko.SSHException as e:
            output += '\nError occurred on %s:\n%s\n' % (ip, str(e))
        except socket.timeout:
            output += 'Timeout expired executing command on device %s' % ip
    return output


def write_output(screen_output):
    """ Purpose: This function is called to either print the screen_output to the user, or write it to a file 
               | if we've received a filepath prepended on the output string in between identifiers '*****WRITE_TO_FILE*****'

        @param screen_output: String  containing all the output gathered throughout the script. 
                            | If the user specifies -w, the screen_output string should start with
                            | '*****WRITE_TO_FILE*****path/to/output/file.txt*****WRITE_TO_FILE*****' so that this function
                            | can find where to write the file without needing another argument. 
        @type screen_output: str

        @returns: None
    """
    if "*****WRITE_TO_FILE*****" in screen_output:
        write_to_file = screen_output.split('*****WRITE_TO_FILE*****')[1]
        style = screen_output.split('*****WRITE_TO_FILE*****')[2]
        screen_output = screen_output.split('*****WRITE_TO_FILE*****')[3]
        # open the output file if one was specified.
        if style.lower() in ["s", "single"]:
            try:
                # mode 'a' is append mode, 'b' is for binary files and windows compatibility.
                out_file = open(write_to_file, 'a+b')
            except IOError as e:
                print('Error opening output file \'%s\' for writing. Here is the output that would\'ve been written:\n' % write_to_file)
                print(screen_output)
                print('\n\nHere is the error for opening the output file:')
                raise e
            else:
                out_file.write('%s\n\n' % screen_output)
                print('\nOutput written/appended to: ' + write_to_file)
        elif style.lower() in ["m", "multiple"]:
            ip = screen_output.split('device: ')[1].split('\n')[0].strip()
            try:
                filepath = path.join(path.split(write_to_file)[0], ip + "_" + path.split(write_to_file)[1])
                out_file = open(filepath, 'a+b')
            except IOError as e:
                print('Error opening output file \'%s\' for writing. Here is the output that would\'ve been written:\n' % write_to_file)
                print(screen_output)
                print('\n\nHere is the error for opening the output file:')
                raise e
            else:
                out_file.write(screen_output)
                print('\nOutput written/appended to: ' + filepath)
                out_file.close()

    # --scp function copy_file will return '' if we aren't writing to a file, because the output is printed to the user immediately
    # Therefore we don't need to output anything here if we have received empty quotes. 
    elif screen_output != '':
        print(screen_output)
