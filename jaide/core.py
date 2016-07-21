"""
This core.py module is part of the Jaide (Junos Aide) package.

It is free software for use in manipulating junos devices. To immediately get
started, take a look at the example files for implementation
guidelines. More information can be found at the github page found here:

https://github.com/NetworkAutomation/jaide
"""
# This is for modifying printed output (used for --scp to rewrite the same line
# multiple times.) It is required to be at the top of the file.
from __future__ import print_function
# standard modules.
from os import path
import time
import difflib
# from lxml import etree, objectify
# needed to parse strings into xml for cases when ncclient doesn't handle
# it (commit, validate, etc)
import xml.etree.ElementTree as ET
import logging  # logging needed for disabling paramiko logging output
# intra-Jaide imports
from errors import InvalidCommandError
from utils import clean_lines, xpath
# network modules for device connections
try:
    from ncclient import manager
    from scp import SCPClient
    import paramiko
except ImportError as e:
    print("FAILED TO IMPORT ONE OR MORE PACKAGES.\n"
          "NCCLIENT\thttps://github.com/leopoul/ncclient/\n"
          "PARAMIKO\thttps://github.com/paramiko/paramiko\n"
          "SCP\t\thttps://pypi.python.org/pypi/scp/0.8.0")
    print('\nImport Error:\n')
    raise e


class Jaide():

    """ Purpose: An object for manipulating a Junos device.

    Methods include copying files, running show commands,
    shell commands, commit configuration changes, finding
    interface errors, and getting device status/information.

    All of the methods listed below that touch Junos are wrapped by a
    decorator function @check_instance, which handles ensuring the correct
    connection is used to perform the requested operation.
    """
    def __init__(self, host, username, password, connect_timeout=5,
                 session_timeout=300, connect="paramiko", port=22):
        """ Initialize the Jaide object.

        Purpose: This is the initialization function for the Jaide class,
               | which creates a connection to a junos device. It will
               | return a Jaide object, which can then be used to actually
               | send commands to the device. This function establishes the
               | connection to the device via a NCClient manager object.
               | > **NOTE:** The connect parameter should be ignored under most
               | > circumstances. Changing it only affects how Jaide first
               | > connects to the device. The decorator function
               | > @check_instance will handle moving between session
               | > types for you.

        @param host: The IP or hostname of the device to connect to.
        @type host: str
        @param username: The username for the connection
        @type username: str
        @param password: The password for the connection
        @type password: str
        @param connect_timeout: The timeout value, in seconds, for attempting
                              | to connect to the device.
        @type connect_timeout: int
        @param session_timeout: The timeout value, in seconds, for the
                              | session. If a command is sent and nothing
                              | is heard back from the device in this
                              | timeframe, the session is declared dead,
                              | and times out.
        @type session_timeout: int
        @param connect: **NOTE: We default to 'paramiko', but this
                        | parameter can be set to False to prevent connecting
                        | on object instantiation. The @check_instance
                        | decorator function will handle sliding between
                        | session types depending on what function is being
                        | called, meaning generally self.conn_type and this
                        | connect parameter should be ignored.**
                        |
                        | The connection type that should be made. Several
                        | options are available: 'ncclient', 'scp', and
                        | 'paramiko', 'shell' and 'root'.
                        |
                        | 'paramiko' : is used for operational commands
                        | (couldn't use ncclient because of lack of pipes `|`
                        | support.
                        |
                        | 'scp' : is used for copying files to/from
                        | the device, and uses an SCP connection.
                        |
                        | 'shell' : is for sending shell commands.
                        |
                        | 'root' : is when the user is doing operational
                        | commands, but is logged in as root, (requires
                        | handling separately, since this puts the session
                        | into a shell prompt)
                        |
                        | 'ncclient' : is used for all other commands.
        @type connect: str
        @param port: The destination port on the device to attempt the
                   | connection.
        @type port: int

        @returns: an instance of the Jaide class
        @rtype: jaide.Jaide object
        """
        # store object properties and set initial values.
        self.host = host.strip()
        self.port = port
        self.username = username
        self.password = password
        self.session_timeout = session_timeout
        self.connect_timeout = connect_timeout
        self._shell = ""
        self._scp = ""
        self.conn_type = connect
        self._in_cli = False
        self._filename = None
        # make the connection to the device
        if connect:
            self.connect()

    def check_instance(function):
        """ Wrapper that tests the type of _session.

        Purpose: This decorator function is used by all functions within
              | the Jaide class that interact with a device to ensure the
              | proper session type is in use. If it is not, it will
              | attempt to migrate _session to that type before moving
              | to the originally requested function.
              | > **NOTE:** This function is a decorator, and should not be
              | >  used directly. All other methods in this class that touch
              | >  the Junos device are wrapped by this function to ensure the
              | >  proper connection type is used.

        @param function: the function that is being wrapped around
        @type function: function

        @returns: the originally requested function
        @rtype: function
        """
        def wrapper(self, *args, **kwargs):
            func_trans = {
                "commit": manager.Manager,
                "compare_config": manager.Manager,
                "commit_check": manager.Manager,
                "device_info": manager.Manager,
                "diff_config": manager.Manager,
                "health_check": manager.Manager,
                "interface_errors": manager.Manager,
                "op_cmd": paramiko.client.SSHClient,
                "shell_cmd": paramiko.client.SSHClient,
                "scp_pull": paramiko.client.SSHClient,
                "scp_push": paramiko.client.SSHClient
            }
            # when doing an operational command, logging in as root
            # brings you to shell, so we need to enter the device as a shell
            # connection, and move to cli to perform the command
            # this is a one-off because the isinstance() check will be bypassed
            if self.username == "root" and function.__name__ == "op_cmd":
                if not self._session:
                    self.conn_type = "paramiko"
                    self.connect()
                if not self._shell:
                    self.conn_type = "root"
                    self.connect()
                self.shell_to_cli()  # check if we're in the cli
            # Have to call shell command separately, since we are using _shell
            # for comparison, not _session.
            elif function.__name__ == 'shell_cmd':
                if not self._shell:
                    self.conn_type = "shell"
                    self.connect()
                self.cli_to_shell()  # check if we're in shell.
            if isinstance(self._session, func_trans[function.__name__]):
                # If they're doing SCP, we have to check for both _session and
                # _scp
                if function.__name__ in ['scp_pull', 'scp_push']:
                    if not isinstance(self._scp, SCPClient):
                        self.conn_type = "scp"
                        self.connect()
            else:
                self.disconnect()
                if function.__name__ == "op_cmd":
                    self.conn_type = "paramiko"
                elif function.__name__ in ["scp_pull", "scp_push"]:
                    self.conn_type = "scp"
                else:
                    self.conn_type = "ncclient"
                self.connect()
            return function(self, *args, **kwargs)
        return wrapper

    def cli_to_shell(self):
        """ Move _shell to the shell from the command line interface (CLI). """
        if self._in_cli:
            self._shell.send("start shell\n")
            time.sleep(2)
            self._shell.recv(9999)
            self._in_cli = False
            return True
        return False

    @check_instance
    def commit(self, commands="", confirmed=None, comment=None,
               at_time=None, synchronize=False, req_format='text', action="set", config_format="text"):
        """ Perform a commit operation.

        Purpose: Executes a commit operation. All parameters are optional.
               | commit confirm and commit at are mutually exclusive. All
               | the others can be used with each other and commit confirm/at.

        @param commands: A string or list of multiple commands
                       | that the device will compare with.
                       | If a string, it can be a single command,
                       | multiple commands separated by commas, or
                       | a filepath location of a file with multiple
                       | commands, each on its own line.
        @type commands: str or list
        @param confirmed: integer value of the number of **seconds** to
                             | confirm the commit for, if requested.
        @type confirmed: int
        @param comment: string that the user wants to comment the commit
                      | with. Will show up in the 'show system commit' log.
        @type comment: str
        @param at_time: string designating the time at which the commit
                      | should happen. Can be in one of two Junos approved
                      | formats.
        @type comment: str
        @param synchronize: boolean set to true if desiring a commit
                          | synchronize operation.
        @type synchronize: bool
        @param req_format: string to specify the response format. Accepts
                         | either 'text' or 'xml'
        @type req_format: str

        @returns: The reply from the device.
        @rtype: str
        """
        # ncclient doesn't support a truly blank commit, so if nothing is
        # passed, use 'annotate system' to make a blank commit
        if not commands:
            commands = 'annotate system ""'
        if config_format == "text":
            clean_cmds = []
            for cmd in clean_lines(commands):
                clean_cmds.append(cmd)
        else:
            clean_cmds = commands
        # try to lock the candidate config so we can make changes.
        self.lock()
        self._session.load_configuration(action=action, config=clean_cmds, format=config_format)
        results = ""
        # confirmed and commit at are mutually exclusive. commit confirm
        # takes precedence.
        if confirmed:
            results = self._session.commit(confirmed=True,
                                           timeout=str(confirmed),
                                           comment=comment,
                                           synchronize=synchronize)
        else:
            results = self._session.commit(comment=comment, at_time=at_time,
                                           synchronize=synchronize)
        self.unlock()
        if results:
            if req_format == 'xml':
                return results
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
                elif i.tag == 'ok':
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

    @check_instance
    def commit_check(self, commands="", req_format="text", action="set", config_format="text"):
        """ Execute a commit check operation.

        Purpose: This method will take in string of multiple commands,
               | and perform and 'commit check' on the device to ensure
               | the commands are syntactically correct. The response can
               | be formatted as text or as xml.

        @param commands: A string, filepath, or list of multiple commands
                       | that the device will compare with.
        @type commands: str or list
        @param req_format: The desired format of the response, defaults to
                         | 'text', but also accepts 'xml'
        @type req_format: str

        @returns: The reply from the device.
        @rtype: str
        """
        if not commands:
            raise InvalidCommandError('No commands specified')
        if config_format == 'text':
            clean_cmds = []
            for cmd in clean_lines(commands):
                clean_cmds.append(cmd)
        else:
            clean_cmds = commands
        self.lock()
        self._session.load_configuration(action=action, config=clean_cmds, format=config_format)
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
    def compare_config(self, commands="", req_format="text", action="set", config_format="text"):
        """ Execute a 'show | compare' against the specified commands.

        Purpose: This method will take in string of multiple commands,
               | and perform and 'show | compare' on the device to show the
               | differences between the active running configuration and
               | the changes proposed by the passed commands parameter.

        @param commands: A string, filepath, or list of multiple commands
                       | that the device will compare with.
        @type commands: str or list
        @param req_format: The desired format of the response, defaults to
                         | 'text', but also accepts 'xml'
        @type req_format: str

        @returns: The reply from the device.
        @rtype: str
        """
        if not commands:
            raise InvalidCommandError('No commands specified')
        if config_format == "text":
            clean_cmds = [cmd for cmd in clean_lines(commands)]
        else:
            clean_cmds = commands
        self.lock()
        self._session.load_configuration(action=action, config=clean_cmds, format=config_format)
        out = self._session.compare_configuration()
        self.unlock()
        if req_format.lower() == "xml":
            return out
        return out.xpath(
            'configuration-information/configuration-output')[0].text

    def connect(self):
        """ Establish a connection to the device.

        Purpose: This method is used to make a connection to the junos
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
            logger = logging.Logger.manager.getLogger('paramiko.transport')
            logger.setLevel(logging.CRITICAL)
            self._session.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
            self._session.connect(hostname=self.host,
                                  username=self.username,
                                  password=self.password,
                                  port=self.port,
                                  timeout=self.connect_timeout)
        if self.conn_type == 'scp':
            self._scp_session = paramiko.SSHClient()
            logger = logging.Logger.manager.getLogger('paramiko.transport')
            logger.setLevel(logging.CRITICAL)
            self._scp_session.set_missing_host_key_policy(
                paramiko.AutoAddPolicy())
            self._scp_session.connect(hostname=self.host,
                                      username=self.username,
                                      password=self.password,
                                      port=self.port,
                                      timeout=self.connect_timeout)
            self._scp = SCPClient(self._scp_session.get_transport())
        elif self.conn_type == "ncclient":
            self._session = manager.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.connect_timeout,
                device_params={'name': 'junos'},
                hostkey_verify=False
            )
        elif self.conn_type == 'shell':
            if not self._session:
                self.conn_type = 'paramiko'
                self.connect()
                self.conn_type = 'shell'
            if not self._shell:
                self._shell = self._session.invoke_shell()
                time.sleep(2)
                if self.username != 'root' and not self._in_cli:
                    self._in_cli = True
            if not self.cli_to_shell():
                self._shell.recv(9999)
        elif self.conn_type == 'root':
            # open the shell if necessary, and move into CLI
            if not self._shell:
                self._shell = self._session.invoke_shell()
                time.sleep(2)
            if not self.shell_to_cli():
                self._shell.recv(9999)
        self._update_timeout(self.session_timeout)

    def _copy_status(self, filename, size, sent):
        """ Echo status of an SCP operation.

        Purpose: Callback function for an SCP operation. Used to show
               | the progress of an actively running copy. This directly
               | prints to stdout, one line for each file as it's copied.
               | The parameters received by this function are those received
               | from the scp.put or scp.get function, as explained in the
               | python scp module docs.

        @param filename: The filename of file being copied.
        @type filename: str
        @param size: The total size of the current file being copied.
        @type size: str or float
        @param sent: The amount of data sent for the current file being copied.
        @type sent: str or float

        @returns: None
        """
        output = "Transferred %.0f%% of the file %s" % (
            (float(sent) / float(size) * 100), path.normpath(filename))
        output += (' ' * (120 - len(output)))
        if filename != self._filename:
            if self._filename is not None:
                print('')
            self._filename = filename
        print(output, end='\r')

    @check_instance
    def device_info(self):
        """ Pull basic device information.

        Purpose: This function grabs the hostname, model, running version, and
               | serial number of the device.

        @returns: The output that should be shown to the user.
        @rtype: str
        """
        # get hostname, model, and version from 'show version'
        resp = self._session.get_software_information(format='xml')
        hostname = resp.xpath('//software-information/host-name')[0].text
        model = resp.xpath('//software-information/product-model')[0].text
        version = (resp.xpath('//software-information/package-information/'
                              'comment')[0].text.split('[')[1].split(']')[0])
        # get uptime from 'show system uptime'
        resp = self._session.get_system_uptime_information(format='xml')
        current_time = resp.xpath('//current-time/date-time')[0].text
        uptime = resp.xpath('//uptime-information/up-time')[0].text
        # get serial number from 'show chassis hardware'
        show_hardware = self._session.get_chassis_inventory(format='xml')
        # If we're hitting an EX, grab each Routing Engine Serial number
        # to get all RE SNs in a VC
        if (('EX' or 'ex' or 'Ex') in
            show_hardware.xpath('//chassis-inventory/chassis/chassis-module'
                                '/description')[0].text):
            serial_num = ""
            for eng in show_hardware.xpath('//chassis-inventory/chassis/chassis-module'):
                if 'Routing Engine' in eng.xpath('name')[0].text:
                    serial_num += (eng.xpath('name')[0].text + ' Serial #: ' +
                                   eng.xpath('serial-number')[0].text)
        else:  # Any other device type, just grab chassis SN
            serial_num = ('Chassis Serial Number: ' +
                          show_hardware.xpath('//chassis-inventory/chassis/'
                                              'serial-number')[0].text)
        return ('Hostname: %s\nModel: %s\nJunos Version: %s\n%s\nCurrent Time:'
                ' %s\nUptime: %s\n' %
                (hostname, model, version, serial_num, current_time, uptime))

    # TODO: [2.1] @rfe optional different username/password.
    @check_instance
    def diff_config(self, second_host, mode='stanza'):
        """ Generate configuration differences with a second device.

        Purpose: Open a second ncclient.manager.Manager with second_host, and
               | and pull the configuration from it. We then use difflib to
               | get the delta between the two, and yield the results.

        @param second_host: the IP or hostname of the second device to
                          | compare against.
        @type second_host: str
        @param mode: string to signify 'set' mode or 'stanza' mode.
        @type mode: str

        @returns: iterable of strings
        @rtype: str
        """
        second_conn = manager.connect(
            host=second_host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=self.connect_timeout,
            device_params={'name': 'junos'},
            hostkey_verify=False
        )

        command = 'show configuration'
        if mode == 'set':
            command += ' | display set'

        # get the raw xml config
        config1 = self._session.command(command, format='text')
        # for each /configuration-output snippet, turn it to text and join them
        config1 = ''.join([snippet.text.lstrip('\n') for snippet in
                          config1.xpath('//configuration-output')])

        config2 = second_conn.command(command, format='text')
        config2 = ''.join([snippet.text.lstrip('\n') for snippet in
                          config2.xpath('//configuration-output')])

        return difflib.unified_diff(config1.splitlines(), config2.splitlines(),
                                    self.host, second_host)

    def disconnect(self):
        """ Close the connection(s) to the device.

        Purpose: Closes the current connection(s) to the device, no matter
               | what types exist.

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
        elif isinstance(self._session, SCPClient):
            self._session.close()
            self._session = ""
            self._scp = ""

    def _error_parse(self, interface, face):
        """ Parse the extensive xml output of an interface and yield errors.

        Purpose: Takes the xml output of 'show interfaces extensive' for a
               | given interface and yields the error types that have a
               | significant number of errors.

        @param interface: The xml output of the 'sh int ext' command for
                        | the desired interface.
        @type interface: lxml.etree._Element object
        @param face: The direction of the errors we're wanting. Either 'input'
                   | or 'output' is accepted.
        @type face: str

        @returns: Yields each error that has a significant number
        @rtype: iterable of strings.
        """
        try:
            error_list = interface.xpath(face + '-error-list')[0].getchildren()
        except IndexError:  # no error list on this interface
            pass
        else:
            for x in range(len(error_list)):
                if error_list[x].tag == "carrier-transitions":
                    if int(error_list[x].text.strip()) > 50:
                        yield " has greater than 50 flaps."
                elif int(error_list[x].text.strip()) > 0:
                    yield " has %s of %s." % (error_list[x].text.strip(),
                                              error_list[x].tag.strip())

    @check_instance
    def health_check(self):
        """ Pull health and alarm information from the device.

        Purpose: Grab the cpu/mem usage, system/chassis alarms, top 5
               | processes, and states if the primary/backup partitions are on
               | different versions.

        @returns: The output that should be shown to the user.
        @rtype: str
        """
        output = 'Chassis Alarms:\n\t'
        # Grab chassis alarms, system alarms, show chassis routing-engine,
        # 'show system processes extensive', and also xpath to the
        # relevant nodes on each.
        chassis_alarms = self._session.command("show chassis alarms")
        chassis_alarms = chassis_alarms.xpath('//alarm-detail')
        system_alarms = self._session.command("show system alarms")
        system_alarms = system_alarms.xpath('//alarm-detail')
        chass = self._session.command(command="show chassis routing-engine",
                                      format='text').xpath('//output')[0].text
        proc = self._session.command("show system processes extensive")
        proc = proc.xpath('output')[0].text.split('\n')
        if chassis_alarms == []:  # Chassis Alarms
            output += 'No chassis alarms active.\n'
        else:
            for i in chassis_alarms:
                output += (i.xpath('alarm-class')[0].text.strip() + ' Alarm \t'
                           '\t' + i.xpath('alarm-time')[0].text.strip() +
                           '\n\t' +
                           i.xpath('alarm-description')[0].text.strip() + '\n')
        output += '\nSystem Alarms: \n\t'
        if system_alarms == []:  # System Alarms
            output += 'No system alarms active.\n'
        else:
            for i in system_alarms:
                output += (i.xpath('alarm-class')[0].text.strip() + ' Alarm '
                           '\t\t' + i.xpath('alarm-time')[0].text.strip() +
                           '\n\t' +
                           i.xpath('alarm-description')[0].text.strip() + '\n')
        # add the output of the show chassis routing-engine to the command.
        output += '\n' + chass
        # Grabs the top 5 processes and the header line.
        output += ('\n\nTop 5 busiest processes (high mgd values likely from '
                   'script execution):\n')
        for line_number in range(8, 14):
            output += proc[line_number] + '\n'
        return output

    @check_instance
    def interface_errors(self):
        """ Parse 'show interfaces extensive' and return interfaces with errors.

        Purpose: This function is called for the -e flag. It will let the user
               | know if there are any interfaces with errors, and what those
               | interfaces are.

        @returns: The output that should be shown to the user.
        @rtype: str
        """
        output = []  # used to store the list of interfaces with errors.
        # get a string of each physical and logical interface element
        dev_response = self._session.command('sh interfaces extensive')
        ints = dev_response.xpath('//physical-interface')
        ints += dev_response.xpath('//logical-interface')
        for i in ints:
            # Grab the interface name for user output.
            int_name = i.xpath('name')[0].text.strip()
            # Only check certain interface types.
            if (('ge' or 'fe' or 'ae' or 'xe' or 'so' or 'et' or 'vlan' or
                 'lo0' or 'irb') in int_name):
                try:
                    status = (i.xpath('admin-status')[0].text.strip() +
                              '/' + i.xpath('oper-status')[0].text.strip())
                except IndexError:
                    pass
                else:
                    for error in self._error_parse(i, "input"):
                        output.append("%s (%s)%s" % (int_name, status,
                                                     error))
                    for error in self._error_parse(i, "output"):
                        output.append("%s (%s)%s" % (int_name, status,
                                                     error))
        if output == []:
            output.append('No interface errors were detected on this device.')
        return '\n'.join(output) + '\n'

    def lock(self):
        """ Lock the candidate config. Requires ncclient.manager.Manager. """
        if isinstance(self._session, manager.Manager):
            self._session.lock()

    @check_instance
    def op_cmd(self, command, req_format='text', xpath_expr=""):
        """ Execute an operational mode command.

        Purpose: Used to send an operational mode command to the connected
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
        @type command: str
        @param req_format: The desired format of the response, defaults to
                         | 'text', but also accepts 'xml'. **NOTE**: 'xml'
                         | will still return a string, not a libxml ElementTree
        @type req_format: str

        @returns: The reply from the device.
        @rtype: str
        """
        if not command:
            raise InvalidCommandError("Parameter 'command' cannot be empty")
        if req_format.lower() == 'xml' or xpath_expr:
            command = command.strip() + ' | display xml'
        command = command.strip() + ' | no-more\n'
        out = ''
        # when logging in as root, we use _shell to get the response.
        if self.username == 'root':
            self._shell.send(command)
            time.sleep(3)
            while self._shell.recv_ready():
                out += self._shell.recv(999999)
                time.sleep(.75)
            # take off the command being sent and the prompt at the end.
            out = '\n'.join(out.split('\n')[1:-2])
        # not logging in as root, and can grab the output as normal.
        else:
            stdin, stdout, stderr = self._session.exec_command(command=command,
                                           timeout=float(self.session_timeout))
            stdin.close()
            # read normal output
            while not stdout.channel.exit_status_ready():
                out += stdout.read()
            stdout.close()
            # read errors
            while not stderr.channel.exit_status_ready():
                out += stderr.read()
            stderr.close()
        return out if not xpath_expr else xpath(out, xpath_expr)

    @check_instance
    def scp_pull(self, src, dest, progress=False, preserve_times=True):
        """ Makes an SCP pull request for the specified file(s)/dir.

        Purpose: By leveraging the _scp private variable, we make an scp pull
               | request to retrieve file(s) from a Junos device.

        @param src: string containing the source file or directory
        @type src: str
        @param dest: destination string of where to put the file(s)/dir
        @type dest: str
        @param progress: set to `True` to have the progress callback be
                       | printed as the operation is copying. Can also pass
                       | a function pointer to handoff the progress callback
                       | elsewhere.
        @type progress: bool or function pointer
        @param preserve_times: Set to false to have the times of the copied
                             | files set at the time of copy.
        @type preserve_times: bool

        @returns: `True` if the copy succeeds.
        @rtype: bool
        """
        # set up the progress callback if they want to see the process
        if progress is True:
            self._scp._progress = self._copy_status
        # redirect to another function
        elif hasattr(progress, '__call__'):
            self._scp._progress = progress
        else:  # no progress callback
            self._scp._progress = None
        # retrieve the file(s)
        self._scp.get(src, dest, recursive=True, preserve_times=preserve_times)
        self._filename = None
        return False

    @check_instance
    def scp_push(self, src, dest, progress=False, preserve_times=True):
        """ Purpose: Makes an SCP push request for the specified file(s)/dir.

        @param src: string containing the source file or directory
        @type src: str
        @param dest: destination string of where to put the file(s)/dir
        @type dest: str
        @param progress: set to `True` to have the progress callback be
                       | printed as the operation is copying. Can also pass
                       | a function pointer to handoff the progress callback
                       | elsewhere.
        @type progress: bool or function pointer
        @param preserve_times: Set to false to have the times of the copied
                             | files set at the time of copy.
        @type preserve_times: bool

        @returns: `True` if the copy succeeds.
        @rtype: bool
        """
        # set up the progress callback if they want to see the process
        if progress is True:
            self._scp._progress = self._copy_status
        # redirect to another function
        elif hasattr(progress, '__call__'):
            self._scp._progress = progress
        else:  # no progress callback
            self._scp._progress = None
        # push the file(s)
        self._scp.put(src, dest, recursive=True, preserve_times=preserve_times)
        self._filename = None
        return False

    @check_instance
    def shell_cmd(self, command=""):
        """ Execute a shell command.

        Purpose: Used to send a shell command to the connected device.
               | This uses the self._shell instance, which should be a
               | paramiko.Channel object, instead of a SSHClient.
               | This is because we cannot send shell commands to the
               | device using a SSHClient.

        @param command: The single command that to retrieve output from the
                      | device.
        @type command: str

        @returns: The reply from the device.
        @rtype: str
        """
        if not command:
            raise InvalidCommandError("Parameter 'command' must not be empty.")
        command = command.strip() + '\n'
        self._shell.send(command)
        time.sleep(2)
        out = ''
        while self._shell.recv_ready():
            out += self._shell.recv(999999)
            time.sleep(.75)
        # take off the command being sent and the prompt at the end.
        return '\n'.join(out.split('\n')[1:-1])

    def shell_to_cli(self):
        """ Move _shell to the command line interface (CLI). """
        if not self._in_cli:
            self._shell.send("cli\n")
            time.sleep(4)
            self._shell.recv(9999)
            self._in_cli = True
            return True
        return False

    def unlock(self):
        """ Unlock the candidate config.

        Purpose: Unlocks the candidate configuration, so that other people can
               | edit the device. Requires the _session private variable to be
               | a type of a ncclient.manager.Manager.
        """
        if isinstance(self._session, manager.Manager):
            self._session.unlock()

    def _update_timeout(self, value):
        if isinstance(self._session, manager.Manager):
            self._session.timeout = value
        if self._shell:
            self._shell.settimeout(value)
        # SSHClient not here because timeout is sent with each command.

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
    def connect_timeout(self):
        return self.connect_timeout

    @connect_timeout.setter
    def connect_timeout(self, value):
        self.connect_timeout = value

    @property
    def session_timeout(self):
        return self.session_timeout

    @session_timeout.setter
    def session_timeout(self, value):
        self.session_timeout = value
        self._update_timeout(value)
