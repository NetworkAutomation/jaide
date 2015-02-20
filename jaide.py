"""
This module is the Junos Aide/Jaide/JGUI project.

It is free software for use in manipulating junos devices. To immediately get
started, take a look at the examples or test files for implementation
guidelines. More information can be found at the github page found here:

https://github.com/NetworkAutomation/jaide
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
    from os import path
    import time
    import difflib
    from scp import SCPClient
    import paramiko
    import logging  # logging needed for disabling paramiko logging output
    from errors.errors import InvalidCommandError
except ImportError as e:
    print("FAILED TO IMPORT ONE OR MORE PACKAGES.\n"
          "NCCLIENT\thttps://github.com/leopoul/ncclient/\n"
          "PARAMIKO\thttps://github.com/paramiko/paramiko\n"
          "SCP\t\thttps://pypi.python.org/pypi/scp/0.8.0")
    print('\nImport Error:\n')
    raise e


def clean_lines(commands):
    """ Generate strings that are not comments or lines with only whitespace.

    Purpose: This function is a generator that will read in either a
           | plain text file of strings(IP list, command list, etc), a
           | comma separated string of strings, or a list of strings. It
           | will crop out any comments or blank lines, and yield
           | individual strings.
           |
           | Only strings that do not start with a comment '#', or are not
           | entirely whitespace will be yielded. This allows a file with
           | comments and blank lines for formatting neatness to be used
           | without a problem.

    @param commands: This can be either a string that is a file
                   | location, a comma separated string of strings,
                   | or a python list of strings.
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
        else:  # if a single command, need to just be returned.
            try:
                if commands.strip()[0] != "#":
                    yield commands.strip() + '\n'
                    return
            except IndexError:
                pass
    elif isinstance(commands, list):
        pass
    else:
        raise TypeError('clean_lines() accepts a \'str\' or \'list\'')
    for cmd in commands:
        # exclude commented lines, and skip blank lines (index error)
        try:
            if cmd.strip()[0] != "#":
                yield cmd.strip() + '\n'
        except IndexError:
            pass


def xpath(source_xml, xpath_expr, req_format='string'):
    """ Filter xml based on an xpath expression.

    Purpose: This function applies an Xpath expression to the XML
           | supplied by source_xml. Returns a string subtree or
           | subtrees that match the Xpath expression. It can also return
           | an xml object if desired.

    @param source_xml: Plain text XML that will be filtered
    @type source_xml: str or lxml.etree.ElementTree.Element object
    @param xpath_expr: Xpath expression that we will filter the XML by.
    @type xpath_expr: str
    @param req_format: the desired format of the response, accepts string or
                     | xml.
    @type req_format: str

    @returns: The filtered XML if filtering was successful. Otherwise,
            | an empty string.
    @rtype: str or ElementTree
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
    # Return string from the list of Elements or pure xml
    if req_format == 'xml':
        return filtered_list
    matches = ''.join(etree.tostring(
        element, pretty_print=True) for element in filtered_list)
    return matches if matches else ""


# TODO: config diff (difflib unified_diff()) (in tool)
class Jaide():

    """ Purpose: An object for manipulating a Junos device.

    Methods include copying files, running show commands,
    shell commands, commit configuration changes, finding
    interface errors, and getting device status/information.
    """

    def __init__(self, host, username, password, conn_timeout=5,
                 sess_timeout=300, conn_type="paramiko", port=22):
        """ Initialize the Jaide object.

        Purpose: This is the initialization function for the Jaide class,
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
                        | 'ncclient' is used for all other commands. Even
                        | though we default to paramiko, the @check_instance
                        | decorator function will handle sliding between
                        | session types depending on what function is being
                        | called.
        @type conn_type: str
        @param port: The destination port on the device to attempt the
                   | connection.
        @type port: int

        @returns: an instance of the Jaide class
        @rtype: object
        """
        # store object properties and set initial values.
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sess_timeout = sess_timeout
        self.conn_timeout = conn_timeout
        self._shell = ""
        self._scp = ""
        self.conn_type = conn_type
        self._in_cli = False
        self._filename = ""
        # make the connection to the device
        self.connect()

    def check_instance(function):
        """ Wrapper that tests the type of _session.

        Purpose: This decorator function is used by all functions within
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
                "commit": manager.Manager,
                "compare_config": manager.Manager,
                "commit_check": manager.Manager,
                "dev_info": manager.Manager,
                "diff_config": manager.Manager,
                "health_check": manager.Manager,
                "int_errors": manager.Manager,
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
        """Move _shell to the shell from the command line interface (CLI)."""
        if self._in_cli:
            self._shell.send("start shell\n")
            time.sleep(2)
            self._shell.recv(9999)
            self._in_cli = False
            return True
        return False

    @check_instance
    def commit(self, commit_confirm=None, comment=None, at_time=None,
               synchronize=False, commands="", req_format='text'):
        """ Perform a commit operation.

        Purpose: Executes a commit operation. All parameters are optional.
               | commit confirm and commit at are mutually exclusive. All
               | the others can be used with each other and commit confirm/at.

        @param commit_confirm: integer value of the number of minutes to
                             | confirm the commit for, if requested.
        @type commit_confirm: int
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
        @param commands: A string or list of multiple commands
                       | that the device will compare with.
                       | If a string, it can be a single command,
                       | multiple commands separated by commas, or
                       | a filepath location of a file with multiple
                       | commands, each on its own line.
        @type commands: str or list
        @param req_format: string to specificy the response format. Accepts
                         | either 'text' or 'xml'
        @type req_format: str

        @returns: The reply from the device.
        @rtype: str
        """
        # ncclient doesn't support a truly blank commit, so if nothing is
        # passed, use 'annotate system' to make a blank commit
        if not commands:
            commands = "annotate system"
        clean_cmds = []
        for cmd in clean_lines(commands):
            clean_cmds.append(cmd)
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
            if req_format == 'xml':
                return results
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

    @check_instance
    def commit_check(self, commands="", req_format="text"):
        """ Execute a commit check operation.

        Purpose: This method will take in string of multiple commands,
               | and perform and 'commit check' on the device to ensure
               | the commands are syntactically correct. The response can
               | be formatted as text or as xml.

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
        for cmd in clean_lines(commands):
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
    def compare_config(self, commands="", req_format="text"):
        """ Execute a 'show | compare' against the specified commands.

        Purpose: This method will take in string of multiple commands,
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
        for cmd in clean_lines(commands):
            clean_cmds.append(cmd)
        self.lock()
        self._session.load_configuration(action='set', config=clean_cmds)
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
        if self.conn_type in ['paramiko', 'scp']:
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
            if self.conn_type == 'scp':
                self._scp = SCPClient(self._session.get_transport())
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
            # open the shell if necessary, and move it into CLI
            if not self._shell:
                self._shell = self._session.invoke_shell()
                time.sleep(2)
            if not self.shell_to_cli():
                self._shell.recv(9999)
        self._update_timeout(self.sess_timeout)

    def _copy_status(self, filename, size, sent):
        """ Echo status of an SCP operation.

        Purpose: Callback function for an SCP operation. Used to show
               | the progress of an actively running copy.
        """
        output = "Transferred %.0f%% of the file %s" % (
            (float(sent) / float(size) * 100), path.normpath(filename))
        output += (' ' * (120 - len(output)))
        if filename != self._filename:
            print('')
            self._filename = filename
        print(output, end='\r')

    @check_instance
    def dev_info(self):
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
        # get serial number from 'show chassis hardware'
        show_hardware = self._session.get_chassis_inventory(format='xml')
        # If we're hitting an EX, grab each Routing Engine Serial number
        # to get all RE SNs in a VC
        if ('EX' or 'ex' or 'Ex') in show_hardware.xpath('//chassis-inventory/chassis/chassis-module/description')[0].text:
            serial_num = ""
            for eng in show_hardware.xpath('//chassis-inventory/chassis/chassis-module'):
                if 'Routing Engine' in eng.xpath('name')[0].text:
                    serial_num += (eng.xpath('name')[0].text + ' Serial #: '
                                   + eng.xpath('serial-number')[0].text + "\n")
        else:  # Any other device type, just grab chassis SN
            serial_num = ('Chassis Serial Number: ' +
                          show_hardware.xpath('//chassis-inventory/chassis/'
                                              'serial-number')[0].text + "\n")
        return ('Hostname: %s\nModel: %s\nJunos Version: %s\n%s\n' %
                (hostname, model, version, serial_num))

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

        @returns: the string output of the comparison
        @rtype: str
        """
        second_conn = manager.connect(
            host=second_host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=self.conn_timeout,
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
        re_info = self._session.command(command="show chassis routing-engine",
                                        format='xml').xpath('//route-engine')
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
        output += '\nRouting Engine Information:'
        if re_info == []:  # RE information
            output += '\nNo Routing Engines found...\n'
        else:
            for i in re_info:  # loop through all REs for info.
                # for multi-RE systems, print slot and mastership status.
                if i.xpath('slot') != []:
                    output += ('\nRE' + i.xpath('slot')[0].text + 'Status: \t'
                               + i.xpath('status')[0].text + '\n\tMastership: '
                               + '\t' + i.xpath('mastership-state')[0].text)
                # EX/MX cpu/memory response tags
                if i.xpath('memory-buffer-utilization') != []:
                    output += ('\n\tUsed Memory %: \t' +
                               i.xpath('memory-buffer-utilization')[0].text +
                               '\n\tCPU Temp: \t' +
                               i.xpath('cpu-temperature')[0].text)
                # SRX cpu/memory response tags
                if i.xpath('memory-system-total-util') != []:
                    output += ('\n\tUsed Memory %: \t' +
                               i.xpath('memory-system-total-util')[0].text +
                               '\n\tCPU Temp: \t' +
                               i.xpath('temperature')[0].text)
                output += ('\n\tIdle CPU%: \t' + i.xpath('cpu-idle')[0].text)
                # serial number not shown on single RE MX chassis.
                if i.xpath('serial-number') != []:
                    output += ('\n\tSerial Number: \t' +
                               i.xpath('serial-number')[0].text)
                output += ('\n\tLast Reboot: \t' +
                           i.xpath('last-reboot-reason')[0].text +
                           '\n\tUptime: \t' + i.xpath('up-time')[0].text)
        # Grabs the top 5 processes and the header line.
        output += ('\n\nTop 5 busiest processes (high mgd values likely from '
                   'script execution):\n')
        for line_number in range(8, 14):
            output += proc[line_number] + '\n'
        return output

    @check_instance
    def int_errors(self):
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
        return out if not xpath_expr else xpath(out, xpath_expr)

    @check_instance
    def scp_pull(self, src, dest, progress=False):
        """ Purpose: Makes an SCP pull request for the specified file(s)/dir.

        @param src: string containing the source file or directory
        @type src: str
        @param dest: destination string of where to put the file(s)/dir
        @type dest: str
        @param progress: set to true to have the progress callback be
                       | returned as the operation is copying.
        @type progress: bool

        @returns: True if the copy succeeds.
        @rtype: bool
        """
        # set up the progress callback if they want to see the process
        self._scp._progress = self._copy_status if progress else None
        # retrieve the file(s)
        self._scp.get(src, dest, recursive=True, preserve_times=True)
        return True

    @check_instance
    def scp_push(self, src, dest, progress=False):
        """ Purpose: Makes an SCP push request for the specified file(s)/dir.

        @param src: string containing the source file or directory
        @type src: str
        @param dest: destination string of where to put the file(s)/dir
        @type dest: str
        @param progress: set to true to have the progress callback be
                       | returned as the operation is copying.
        @type progress: bool

        @returns: True if the copy succeeds.
        @rtype: bool
        """
        # set up the progress callback if they want to see the process
        self._scp._progress = self._copy_status if progress else None
        # push the file(s)
        self._scp.put(src, dest, recursive=True, preserve_times=True)
        return True

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
        @type: str

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
        out = '\n'.join(out.split('\n')[1:-1])
        return out

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
        """ Unlock the candidate config. Requires ncclient.manager.Manager. """
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
        """ Getter for host. """
        return self.host

    @host.setter
    def host(self, value):
        """ Setter for host. """
        self.host = value

    @property
    def conn_type(self):
        """ Getter for conn_type. """
        return self.conn_type

    @conn_type.setter
    def conn_type(self, value):
        """ Setter for conn_type. """
        self.conn_type = value

    @property
    def username(self):
        """ Getter for username. """
        return self.username

    @username.setter
    def username(self, value):
        """ Setter for username. """
        self.username = value

    @property
    def password(self):
        """ Getter for password. """
        return self.password

    @password.setter
    def password(self, value):
        """ Setter for password. """
        self.password = value

    @property
    def port(self):
        """ Getter for port. """
        return self.port

    @port.setter
    def port(self, value):
        """ Setter for port. """
        self.port = value

    @property
    def conn_timeout(self):
        """ Getter for conn_timeout. """
        return self.conn_timeout

    @conn_timeout.setter
    def conn_timeout(self, value):
        """ Setter for conn_timeout. """
        self.conn_timeout = value

    @property
    def sess_timeout(self):
        """ Getter for sess_timeout. """
        return self.sess_timeout

    @sess_timeout.setter
    def sess_timeout(self, value):
        """ Setter for sess_timeout. """
        self.sess_timeout = value
