"""
This jaide.py script is intended for use by network administrators with Junos devices to be able to 
manipulate or retrieve information from many devices very quickly and easily. For expansive information 
on the Jaide script, and how JGUI interacts with it, refer to the readme file.

We have provided some information about NCClient here, since it can get confusing in some situations. 

NCClient Information:
    manager.command() can be run with format = 'xml' or 'text', and returns an XML object or string

    manager.command() returns an NCElement object with a .tostring attribute and an xpath() function

    Using .tostring will return a text string of the values of all leaves within the xml tree.

    Using xpath() will return an array of xml leaves, that each has the text property for returning 
    the value of a leaf.

    By default, a show config command run on JUNOS does not return with full XML tags.
    To do xpath on a show config command, explicitly include '| display xml' on the end of the command
     before handing off to manager.command().

    On Junos, non-config commands can be run with '| display xml rpc' appended to get the rpc command.
"""
# This is for modifying printed output (used for --scp to rewrite the same line multiple times.)
# It is required to be at the top of the file. 
from __future__ import print_function  

# Imports:
try:
    from ncclient import manager
    import xml.etree.ElementTree as ET  # needed to parse strings into xml for cases when ncclient doesn't handle it (commit, validate, etc)
    from ncclient.operations.rpc import RPCError  # RPCErrors are returned in certain instances, such as when the candidate config is locked because someone is editing it.
    from ncclient.transport import errors
    import argparse  # for parsing command line arguments.
    import getpass  # for retrieving password input from the user without echoing back what they are typing.
    import multiprocessing  # for running multiple processes simultaneously.
    from os import path
    import paramiko
    import logging  # logging needed for disabling paramiko logging output
    import socket  # used for catching timeout errors on paramiko sessions
    import time
except ImportError as e:
    print("FAILED TO IMPORT ONE OR MORE PACKAGES.\nNCCLIENT\thttps://github.com/leopoul/ncclient/\nPARAMIKO\thttps://github.com/paramiko/paramiko\n\n"
            "For windows users, you will also need PyCrypto:\nPYCRYPTO\thttp://www.voidspace.org.uk/python/modules.shtml#pycrypto"
            "\n\nNote that the --scp command also requires SCP:\n"
            "SCP\t\thttps://pypi.python.org/pypi/scp/0.8.0")
    print('\nScript Error:\n')
    raise e

# -i is a required parameter, the rest are optional arguments
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description="Required Modules:\n\tNCCLIENT - https://github.com/leopoul/ncclient/ \n\tPARAMIKO - https://github.com/paramiko/paramiko \n\tSCP - "
                                "https://pypi.python.org/pypi/scp/ \n\tPyCrypto - http://www.voidspace.org.uk/python/modules.shtml#pycrypto \n\nThis script can be used as an aide to easily do the same command(s) to multiple juniper devices. "
                                 "The only required arguments are the destination IP address(es), and one of the following commands:\nSingle Format: "
                                 "\t[ -c | -e | -H | -I | -s | -S | -l | -b ]\nName Format: \t[ --command | --errors | --health | --info | --set | --scp | --shell | --blank ]",
                                 prog='Jaide', usage="%(prog)s -i IP [-c [operational_mode_commands | file_of_operational_commands] | -e | -H | -I | -s"
                                 " [set_commands | file_of_set_commands] | -S [push | pull] source destination | -l [shell_commands | file_of_shell_commands] | -b]")
parser.add_argument("-i", "--ip", required=True, dest='ip', type=str, help="The target device(s) to run the script against. This can be a single target device IP address, "
                        "a quoted comma separated list of IP's, or a filepath to a file containing IP's on each line. DNS resolution will work using your machine's specified DNS server.")
parser.add_argument("-u", "--username", dest='username', type=str, default='default', help="Username  -  Will prompt if not specified.")
parser.add_argument("-p", "--password", dest='password', type=str, default='default', help="Password  -  Will prompt if not specified.")
parser.add_argument("-w", "--write", dest='write', metavar="OUTPUT_FILENAME", type=str, help="Specify a filename to write any output.")
parser.add_argument("-q", "--quiet", dest='quiet', action="store_true", help="Prevent script from prompting for further user input.")
parser.add_argument("-t", "--timeout", dest="timeout", type=int, default=300, help="Specify the timeout value for the NCClient connection, in seconds."
                    " Default is 300 seconds. This should be increased when no output could be seen for more than 5 minutes (ex. requesting a system snapshot).")

# Script functions: Must select one and only one.
group1 = parser.add_mutually_exclusive_group(required=True)
group1.add_argument("-c", "--command", dest='command', metavar="[operational_mode_commands | file_of_operational_commands]", type=str, help="Send a single operational mode command to device(s).")
group1.add_argument("-e", "--errors", dest='int_error', action='store_true', help='Check all interfaces for errors.')
group1.add_argument("-H", "--health", dest="health_check", action="store_true", help="Grab a Health Check: CPU/Mem usage, alarms, etc from device.")
group1.add_argument("-I", "--info", dest='info', action='store_true', help="Get basic device info (Serial #, Model, etc).")
group1.add_argument("-s", "--set", dest='make_commit', metavar="[set_commands | file_of_set_commands]", type=str, help="Send and commit set command(s) to device(s). "
                    "Can be a single quoted command, a quoted comma separated list of commands, or a file with a list of set commands on each line. Can be used with the commit options --check, --confirm, and --blank.")
group1.add_argument("-S", "--scp", nargs=3, dest="scp", type=str, metavar=("[push | pull]", "source", "destination"), help="The SCP argument -S expects three arguments."
                    " In order, they are the direction 'push' or 'pull', the source file/folder, and the destination file/folder."
                    " For example, this could be used to pull a directory using '--scp pull /var/tmp /path/to/local/destination'")
group1.add_argument("-l", "--shell", dest='shell', metavar="[shell_commands | file_of_shell_commands]", type=str, help="Similar to -c, except it will run the commands from shell instead of operational mode.")
group1.add_argument("-b", "--blank", dest="commit_blank", action='store_true', help="Can be used with or without -s to make a blank commit. A key use case is when trying"
                        " to confirm a commit confirm. --confirm, --check and --blank are mutually exclusive!")

# Commit options. These options are mutually exclusive. 
group2 = parser.add_mutually_exclusive_group()
group2.add_argument("-m", "--confirm", dest='commit_confirm', metavar="CONFIRM_MINUTES", type=int, choices=range(1, 61), help="Can be used with -s to make a confirmed commit. "
                        "Accepts a number in /minutes/ between 1 and 60! --confirm, --check and --blank are mutually exclusive!")
group2.add_argument("-k", "--check", dest="commit_check", action='store_true', help="Can be used with -s to only run a commit check, and not commit the changes."
                        " --confirm, --check and --blank are mutually exclusive!")


def do_netconf(ip, username, password, function, args, write_to_file, timeout=300):
    """ Purpose: To open an NCClient manager session to the device, and run the appropriate function against the device.
        Parameters:
            ip          -   String of the IP of the device, to open the connection, and for logging purposes.
            username    -   The string username used to connect to the device.
            password    -   The string password used to connect to the device.
            function    -   Pointer to function to run after opening connection
            args        -   Args to pass through to function
            write_to_file   -   The filepath specified by the user as to where to place the output from the script. Used to prepend the output
                                string with the filepath, so that the write_output() function can find it easily, without needing another argument. 
            timeout     -   Sets netconf timeout. Defaults to 300 seconds. A higher value may be desired for long running commands, 
                            such as 'request system snapshot slice alternate'
    """
    user_output = ""
    if write_to_file:  # this is used to track the filepath that we will output to. The write_output() function will pick this up. 
        user_output += "*****WRITE_TO_FILE*****" + write_to_file + "*****WRITE_TO_FILE*****"
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
        user_output += '=' * 50 + '\nUnable to connect to device: %s on port: 22\n' % ip
    except errors.AuthenticationError:  # NCClient auth failure
        user_output += '=' * 50 + '\nAuthentication failure for device: %s\n' % ip
    except paramiko.AuthenticationException:  # Paramiko auth failure
        user_output += '=' * 50 + '\nAuthentication failure for device: %s\n' % ip
    except paramiko.SSHException as e:
        user_output += '=' * 50 + '\nError connecting to %s\n:%s' % (ip, str(e))
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
    """ Purpose: This is the callback function for --scp. It will update the user to the status of the current file being transferred. 
    """
    global gbl_filename  # Grab the global variable for the filename being transferred. 
    # does the logic to get an accurate percentage of the amount sent of the current file.
    output = "Transferred %.0f%% of the file %s" % ((float(sent) / float(size) * 100), filename)
    # appends whitespace to the end of the string up to the 120th column, so that the output doesn't look garbled from previous output. 
    output = output + (' ' * (120 - len(output)))
    # If the filename has changed, move to the next line and update the filename. 
    if filename != gbl_filename:
        print('')
        gbl_filename = filename
    # prints the output, end='\r' ends lines with a carriage return instead of new line, 
    # so that the output constantly rewrites the same line (for the current file). This line is what requires the import
    # for 'from __future__ import print_function' 
    print(output, end='\r')


def copy_file(scp_source, scp_dest, ip, username, password, direction, write, multi=False, callback=copy_status):
    """ Purpose: This is the function to scp a file from the specified source and destinations
        Parameters:
            scp_source  -   source file for the SCP transaction
            scp_dest    -   destination file for the SCP transaction
            ip          -   the remote IP address for the SCP transaction
            username    -   the username for the remote device.
            password    -   the password for the remote device.
            direction   -   the direction of the copy operation, either push or pull.
            write       -   The copy_file function is unique in that since it uses callback, it needs to be aware
                            if we are outputting to a file later. If we are, then suppress certain output. If we
                            aren't writing to a file, this function will print updates immediately, and return an 
                            empty string to write_output(), since we've already printed everything to the user. 
            multi       -   Flag should be set to true when sending to multiple devices. This is used to determine 
                            the naming scheme of the destination files. 
            callback    -   definition of callback function to be used by Paramiko for status updates. This is only
                            used when scp'ing to/from a single device, and generally should be passed None otherwise.
    """
    try: 
        # scp is also imported.
        from scp import SCPClient
        from scp import SCPException
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
    # This will make the connection and handle errors Authentication or rejection errors. 
    screen_output = ('=' * 50 + '\nResults from device: %s\n' % ip)
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
        if isinstance(write, basestring):
            screen_output += "*****WRITE_TO_FILE*****" + write + "*****WRITE_TO_FILE*****"
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
                # If callback is something other than None, we are running against one device, and will be printing status output.
                # So we must add a leading \n to move below the callback output. 
                if callback != None:  
                    temp_output = '\n'
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
                if callback != None:
                    temp_output = '\n'  # Newline required to step below callback copy_status() output. 
                temp_output += 'Pushed %s to %s:%s\n' % (scp_source, ip, scp_dest)
        screen_output += temp_output
        return screen_output


def dev_info(conn, ip):
    """ Purpose: This is the function called by using the --info flag on the command line.
                 It grabs the hostname, model, running version, and serial number of the device.
        Parameters:
            conn  -  This is the ncclient manager connection to the remote device.
            ip    -  String containing the IP of the remote device, used for logging purposes.
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
                 It grabs the cpu/mem usage, system/chassis alarms, top 5 processes, if the primary/backup partitions are on different versions.
        Parameters:
            conn    -  This is the ncclient manager conn to the remote device.
            ip      -  String containing the IP of the remote device, used for logging purposes.
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
        Parameters:
            conn  -   The NCClient manager connection to the remote device.
            ip    -   String containing the IP of the remote device, used for logging purposes.
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


def make_commit(conn, ip, commands, commit_check, quiet, commit_confirm, commit_blank):
    """ Purpose: This function will send set command(s) to a device, and commit the change. It can be called by any function that 
                 needs to commit, currently used by the -s flag. The commit can be modified to be just a commit check 
                 with the --check flag, and commit confirm with the --confirm flag. It takes a single string for one set command, or a list of 
                 strings for multiple commands to be committed. 
        Parameters:
            conn        -   The NCClient manager connection to the remote device.
            ip          -   String containing the IP of the remote device, used for logging purposes.
            commands    -   String containing the set command to be sent to the device, or a list of strings of multiple set commands.
                            Either way, the function will respond accordingly, and only one commit will take place.
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
                # commit() expects a timeout in seconds, but users are used to minutes in junos, so convert it to seconds.
                confirm_timeout = str(commit_confirm * 60)
                try:
                    results = conn.commit(confirmed=True, timeout=confirm_timeout)
                except RPCError as e:
                    screen_output += 'Commit could not be completed on this device, due to the following error: \n' + str(e)
            else:  # If they didn't want commit confirm, just straight commit dat shit.
                screen_output += "Attempting to commit on device: %s\n" % ip
                try:
                    results = conn.commit()
                except RPCError as e:
                    screen_output += 'Commit could not be completed on this device, due to the following error: \n' + str(e)
            # conn.commit() DOES NOT return a parse-able xml tree, so we convert it to an ElementTree xml tree.
            if results:
                results = ET.fromstring(results.tostring)
                # This check is for if the commit was successful or not, and update the user accordingly.
                if results.find('commit-check-success') is None:  # None is returned for elements found without a subelement, as in this case.
                    if commit_confirm:
                        screen_output += 'Commit complete on device: %s. It will be automatically rolled back in %s minutes, unless you commit again.\n' % (ip, str(commit_confirm))
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
    # RPC error is received when the configuration database is changed, meaning someone is actively editing the config. 
    # We've already let the user know, so just need to pass.
    except RPCError:
        pass
    conn.close_session()
    return screen_output


def multi_cmd(conn, ip, commands, shell, timeout=300):
    """ Purpose: This function will determine if we are trying to send multiple commands to a device. It is used when the 
                 -c flag is used. If we have more than one command to get output for, then we need to split up the commands
                  and run them individually. Otherwise, we just send the one command. No matter how they sent the command(s)
                  to us (list, filepath, or single command), we take that information and turn it into a list of command(s).
                  We then loop over the list, running run_cmd() for each one. 
        Parameters:
            conn        -   The NCClient manager connection to the remote device.
            ip          -   The IP address of the remote device, for logging.
            commands    -   String containing one of three things: 
                            A single operational show command.
                            a comma separated list of show commands.
                            A filepath pointing to a file with a show command on each line. 
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
        if cmd.strip() != "":
            if cmd.strip()[0] != "#":
                # make sure operational commands don't hold output
                if not shell:
                    cmd = cmd.strip() + " | no-more\n"
                else:  # make sure shell commands end in '\n', so the command will actually send.
                    cmd = cmd.strip() + "\n"
                screen_output += '\n> ' + cmd + run_cmd(conn, ip, cmd, timeout)
    conn.close_session()
    return screen_output


def run_cmd(conn, ip, command, timeout=300):
    """ Purpose: For the -c flag, this function is called. It will connect to a device, run the single specified command, and return the output.
                 There is logic to see if the connection we are receiving is a type of paramiko.Channel. If so, we logged in as root, and had
                 to get to the CLI first, meaning we execute the command using send() rather than exec_command(). Unfortunately, exec_command()
                 couldn't handle getting into CLI, so we needed a method for handling if the user is logging in as root and reaching shell first.
        Parameters:
            conn        -   The NCClient manager connection to the remote device.
            ip          -   String containing the IP of the remote device, used for logging purposes.
            command     -   String containing the command to be sent to the device.
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
    else:
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
                 if they've flagged '-w /path/to/output/file.txt' in the run command.
        Parameters:
            screen_output  -  String or list of strings containing all the output gathered throughout the script. 
                              If the user specifies -w, the screen_output string should start with
                              '*****WRITE_TO_FILE*****path/to/output/file.txt*****WRITE_TO_FILE*****' so that this function
                              can find where to write the file without needing another argument. 
    """
    if "*****WRITE_TO_FILE*****" in screen_output:
        write_to_file = screen_output.split('*****WRITE_TO_FILE*****')[1]
        screen_output = screen_output.split('*****WRITE_TO_FILE*****')[2]
        # open the output file if one was specified.
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
    # --scp function copy_file will return '' if we aren't writing to a file, because the output is printed to the user immediately
    # Therefore we don't need to output anything here if we have received empty quotes. 
    elif screen_output != '':
        print(screen_output)


##########################
# Start of script proper #
##########################
if __name__ == '__main__':
    # Verify requirements.
    args = parser.parse_args()
    if args.scp and (args.scp[0].lower() != 'pull' and args.scp[0].lower() != 'push'):
        parser.error('When using the --scp flag, you must specify the direction as the first argument. For example: "--scp pull /var/tmp /path/to/local/folder"')

    # Check if the username and password are the defaults. If they are, we'll prompt the user for them.
    if args.username == 'default':
        args.username = raw_input("Username: ")
    if args.password == 'default':
        args.password = getpass.getpass()  # getpass will not echo any input back to the user, for safe password entry.
    
    # Correlates argument with function pointer
    function_translation = {
        "command" : multi_cmd,
        "commit_blank" : make_commit,
        "int_error" : int_errors,
        "health_check" : health_check,
        "info" : dev_info,
        "make_commit" : make_commit,
        "shell" : multi_cmd
    }
    # Correlates which args need to be sent to do_netconf based on which feature is being used
    # Must be enclosed in brackets, otherwise argument unpacking will mess it up
    args_translation = {
        "command" : [args.command, False, args.timeout],
        "int_error" : None,
        "health_check" : None,
        "info" : None,
        "make_commit" : [args.make_commit, args.commit_check, args.quiet, args.commit_confirm, args.commit_blank],
        "commit_blank" : [args.make_commit, args.commit_check, args.quiet, args.commit_confirm, args.commit_blank],
        "shell" : [args.shell, True, args.timeout]
    }
   
    # Compares args to function_translation to figure out which we are doing
    # then looks up the function pointer and arguments
    # vars(args) will convert the Namespace from argparser in to a dictionary we can iderate over
    for key in vars(args).keys():
        if key in function_translation:
            if vars(args)[key] is not None and vars(args)[key] is not False:
                function = function_translation[key]
                argsToPass = args_translation[key]

    iplist = ""  # initialize iplist to empty quotes, so we can test it later to see if we have multiple IP's to run against. 
    if len(args.ip.split(',')) > 1:  # Split the IP argument based on commas to see if there is more than one. 
        iplist = args.ip.split(',')
    elif path.isfile(args.ip):  # regex check for a filename, to see if we need to open it. 
        try:
            iplist = open(args.ip, 'rb')  # open the iplist in read only mode, the 'b' is for windows compatibility. 
        except IOError as e:
            print('Couldn\'t open the IP list file %s due to the error:\n' % args.ip)
            raise e
    if args.scp:
        print ("Starting Copy...")  # Needed more output for the user experience. 
    if iplist != "":  # We have matched for multiple IPs, and need to multiprocess.
        # Use # of CPU cores * 2 threads. Cpu_count usually returns double the # of physical cores because of hyperthreading.
        mp_pool = multiprocessing.Pool(multiprocessing.cpu_count()*2)
        for IP in iplist:
            IP = IP.strip()
            if IP != "":  # skip blank lines
                if IP[0] != "#":  # skip comments in an IP list file. 
                    if args.scp:  # scp is handled separately
                        mp_pool.apply_async(copy_file, args=(args.scp[1], args.scp[2], IP, args.username, args.password, args.scp[0], args.write, True, None), callback=write_output)
                    else:
                        mp_pool.apply_async(do_netconf, args=(IP, args.username, args.password, function, argsToPass, args.write, args.timeout), callback=write_output)
        mp_pool.close()
        mp_pool.join()
    else:  # args.ip should be one IP address, and no multiprocessing is required. 
        if args.scp:
            if args.quiet:
                write_output(copy_file(args.scp[1], args.scp[2], args.ip, args.username, args.password, args.scp[0], args.write, False, None))
            else:
                write_output(copy_file(args.scp[1], args.scp[2], args.ip, args.username, args.password, args.scp[0], args.write, False, callback=copy_status))
        else:
            # the do_netconf() will return a string that is passed to the write_output() function for outputting to the user/file.
            write_output(do_netconf(ip=args.ip, username=args.username, password=args.password, function=function, args=argsToPass, write_to_file=args.write, timeout=args.timeout))
