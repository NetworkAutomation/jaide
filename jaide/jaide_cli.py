#!/usr/bin/env python
""" Jaide CLI script for manipulating Junos devices.

This is the cli script that is a base use case of the jaide module.
It is a command line tool, able to be used with the 'jaide' command that is
installed along with the jaide package. It allows for communicating with,
manipulating, and retrieving data from Junos based devices.

For expansive information on the Jaide class, and the jaide CLI tool,
refer to the readme file or the associated examples/documentation. More
information can be found at the github page:

https://github.com/NetworkAutomation/jaide
"""
# standard modules
import sys
import os
from os import path
import multiprocessing
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import getpass
import re
import socket
# intra-Jaide imports
from core import Jaide
from utils import clean_lines
from color_utils import color, strip_color
# The rest are non-standard modules:
from ncclient.transport import errors
from ncclient.operations.rpc import RPCError
from paramiko import SSHException, AuthenticationException
from scp import SCPException

# TODO: --compare argument for doing just comparison without commit checking.
# TODO: use 'click' instead of argparse?
# TODO: Verbosity argument for seeing more/less output?
# TODO: related to above, maybe change --quiet to show nothing?
prs = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                     description="Required Modules:\n\tNCCLIENT - "
                     "https://github.com/leopoul/ncclient/ \n\tPARAMIKO - "
                     "https://github.com/paramiko/paramiko \n\tSCP - "
                     "https://pypi.python.org/pypi/scp/\n\tCOLORAMA - "
                     "https://pypi.python.org/pypi/colorama\n\nThis script can"
                     " be used as an aide to easily do the same command(s) to "
                     "multiple juniper devices. The only required arguments "
                     "are the destination IP address(es) or host(s), and one "
                     "of the following commands:\nSingle Format: "
                     "\t[ -c | -e | -H | -I | -s | -S | -l | -b | -d ]\nName "
                     "Format: \t[ --command | --errors | --health | --info | "
                     "--set | --scp | --shell | --blank | --diff ]",
                     prog='jaide_tool.py', usage="%(prog)s -i IP [-c "
                     "operational_commands | -e | -H | -I | -s "
                     "set_commands | -S [push | pull] source destination | "
                     "-l shell_commands | -b | -d IP [set | stanza] ]")
prs.add_argument("-f", "--format", dest="format", type=str, default='text',
                 metavar='[ text | xml ]', help="Formats output to text or"
                 " xml. Should be used with -c. Default format is text. "
                 "Including an xpath expression after a command forces XML"
                 " output (EX. \"show route %% //rt-entry\").")
prs.add_argument("-i", "--ip", required=True, dest='ip', type=str, help="The "
                 "target device(s) to run the script against. This can be a "
                 "single target device IP address/hostname, a quoted comma "
                 "separated list of IP's, or a filepath to a file containing "
                 "IP's on each line. Hostnames are resolved.")
prs.add_argument("-n", "--no-highlight", dest="no_highlight",
                 action='store_true', help="If flagged, will turn off color "
                 "highlighting in the output. Color highlighting is on by "
                 "default")
prs.add_argument("-p", "--password", dest='password', type=str,
                 default='default', help="Will prompt if not specified.")
prs.add_argument("-P", "--port", dest="port", type=int, default=22,
                 help="Specify the port on which to connect to the device."
                 "Defaults to 22.")
prs.add_argument("-q", "--quiet", dest='quiet', action="store_true", help="Can"
                 " be used with --scp when copying to/from a single device to "
                 "prevent seeing the live status of the transfer.")
prs.add_argument("-t", "--session-timeout", dest="sess_timeout", type=int,
                 default=300, help="Specify the session timeout value, in "
                 "seconds, for declaring a lost session. Default is 300 "
                 "seconds. This should be increased when no output could be "
                 "seen for more than 5 minutes (ex. requesting a system "
                 "snapshot).")
prs.add_argument("-T", "--connection-timeout", dest="conn_timeout", type=int,
                 default=5, help="Specify the connection timeout, in seconds, "
                 "for declaring a device unreachable during connection. "
                 "Default is 5 seconds.")
prs.add_argument("-u", "--username", dest='username', type=str,
                 default='default', help="Will prompt if not specified.")
prs.add_argument("-w", "--write", dest='write', metavar=("[s/single | "
                 "m/multiple]", "OUTPUT_FILENAME"), nargs=2, type=str,
                 help="Specify a filename to write all script output. Also "
                 "requires whether to write to a single file or a separate "
                 "file per IP. (ex. -w s ~/Desktop/output.txt). The output "
                 "format for the names of multiple files is IP_FILENAME.")

# Script functions: Must select one and only one.
group1 = prs.add_mutually_exclusive_group(required=True)
group1.add_argument("-b", "--blank", dest="commit_blank", action='store_true',
                    help="Can be used make a blank commit, which commits with "
                    "no changes. A key use case is when trying to confirm a "
                    "commit confirm. --confirm, --check, --blank, and --at are"
                    " mutually exclusive!")
group1.add_argument("-c", "--command", dest='command', metavar="[operational_"
                    "commands | file_of_operational_commands]", type=str,
                    help="Send single operational mode command(s) to "
                    "device(s). A trailing '%%' followed by an xpath "
                    "expression will filter the xml results by that expression"
                    ". For example: 'show route %% //rt-entry'")
group1.add_argument("-d", "--diff", dest="diff_config", type=str, nargs=2,
                    metavar=("ip_or_hostname", "[set | stanza]"),
                    help="Specify a second IP/host to compare configuration "
                    "between the two different devices, and the configuration "
                    "view mode you would like to see. It will use the same "
                    "username, password, port, and connection timeout as the "
                    "first connection. For example '-d 172.25.1.21 set' or "
                    "'-d switch.domain.com stanza'.")
group1.add_argument("-e", "--errors", dest='int_error', action='store_true',
                    help='Check all interfaces for errors.')
group1.add_argument("-H", "--health", dest="health_check", action="store_true",
                    help="Grab a Health Check: CPU/Mem usage, alarms, etc from"
                    " the device.")
group1.add_argument("-I", "--info", dest='info', action='store_true',
                    help="Get basic device info (Serial #, Model, etc).")
group1.add_argument("-l", "--shell", dest='shell', metavar="[shell_commands | "
                    "file_of_shell_commands]", type=str, help="Similar to -c, "
                    "except it will run the commands from shell instead of "
                    "operational mode.")
group1.add_argument("-s", "--set", dest='make_commit', metavar="[set_commands "
                    "| file_of_set_commands]", type=str, help="Send and commit"
                    " set command(s) to device(s). Can be a single quoted "
                    "command, a quoted comma separated list of commands, or a "
                    "file with a list of set commands on each line. "
                    "Can be used with the commit options --check, --confirm, "
                    "--blank, --comment, --synchronize, and --at.")
group1.add_argument("-S", "--scp", nargs=3, dest="scp", type=str,
                    metavar=("[push | pull]", "source", "destination"),
                    help="The SCP argument -S expects three arguments."
                    " In order, they are the direction 'push' or 'pull', the "
                    "source file/folder, and the destination file/folder. For "
                    "example, this could be used to pull a directory using "
                    "'--scp pull /var/tmp /path/to/local/destination'")

# Commit options. These options are mutually exclusive.
group2 = prs.add_mutually_exclusive_group()
group2.add_argument("-a", "--at", dest='commit_at', type=str,
                    metavar="COMMIT_AT_TIME", help="Specify a time for the "
                    "device to make the commit at. Junos expects one of two "
                    "formats: A time value of the form 'hh:mm[:ss]' or a date "
                    "and time value of the form 'yyyy-mm-dd hh:mm[:ss]' "
                    "(seconds are optional).")
group2.add_argument("-k", "--check", dest="commit_check", action='store_true',
                    help="Can be used with -s to only run a commit check, and"
                    " not commit the changes. --confirm, --check, --blank, and"
                    " --at are mutually exclusive!")
group2.add_argument("-m", "--confirm", dest='confirmed', type=int,
                    metavar="CONFIRM_SECONDS", choices=range(60, 3601),
                    help="Can be used with -s to make a confirmed commit. "
                    "Accepts a number in **seconds** between 60 and 3600! "
                    "--confirm, --check, --blank, and --at are mutually exclusive!")

# Inclusive commit options that can be used with each other and the other
# mutually exclusive options.
group3 = prs.add_argument_group('Inclusive Commit Options', 'Unlike the other '
                                'mutually exclusive commit options, these '
                                'options below can be used with each other or '
                                'together with any other commit option.')
group3.add_argument('-C', '--comment', dest="commit_comment", type=str,
                    help="Add a comment to the commit that will be written to "
                    "the commit log. This should be a quoted string.")
group3.add_argument('-y', '--synchronize', dest="commit_synchronize",
                    action='store_true', help="Enforce a commit synchronize "
                    "operation.")


def open_connection(ip, username, password, function, args, write_to_file,
                    conn_timeout=5, sess_timeout=300, port=22,
                    no_highlight=False):
    """ Open a Jaide session with the device.

    Purpose: To open a Jaide session to the device, and run the
           | appropriate function against the device.

    @param ip: String of the IP of the device, to open the connection
    @type ip: str or unicode
    @param username: The string username used to connect to the device.
    @type useranme: str or unicode
    @param password: The string password used to connect to the device.
    @type password: str or unicode
    @param function: Pointer to function to run after opening connection
    @type function: function
    @param args: Args to pass through to function
    @type args: list
    @param write_to_file: The filepath specified by the user as to where to
                        | place the output from the script. Used to prepend
                        | the output string with the filepath, so that the
                        | write_output() function can find it easily,
                        | without needing another argument.
    @type write_to_file: str or unicode
    @param conn_timeout: Sets the connection timeout value. This is how
                       | we'll wait when connecting before classifying
                       | the device unreachable.
    @type conn_timeout: int
    @param sess_timeout: Sets the session timeout value. A higher value may
                       | be desired for long running commands, such as
                       | 'request system snapshot slice alternate'
    @type sess_timeout: int
    @param no_highlight: the value of the no_highlight argument. Needed to
                      | be returned as part of tuple for passing to the
                      | write_to_file() function
    @type no_highlight: bool

    @returns: a tuple of the output of the jaide command being run, and a
            | boolean whether the output is to be highlighted or not.
    @rtype: (str, bool) tuple
    """
    output = ""
    # this is used to track the filepath that we will output to. The
    # write_output() function will pick this up.
    if write_to_file:
        output += "*****WRITE_TO_FILE*****" + write_to_file[1] + \
                  "*****WRITE_TO_FILE*****" + write_to_file[0] + \
                  "*****WRITE_TO_FILE*****"
    # start with the header line on the output.
    output += color('=' * 50 + '\nResults from device: %s\n' % ip, 'info')
    try:
        # create the Jaide session object for the device.
        conn = Jaide(ip, username, password, connect_timeout=conn_timeout,
                     session_timeout=sess_timeout, port=port)
    except errors.SSHError:
        output += color('Unable to connect to port %s on device: %s\n' %
                        (str(port), ip), 'error')
    except errors.AuthenticationError:  # NCClient auth failure
        output += color('Authentication failed for device: %s\n' % ip, 'error')
    except AuthenticationException:  # Paramiko auth failure
        output += color('Authentication failed for device: %s\n' % ip, 'error')
    except SSHException as e:
        output += color('Error connecting to device: %s\nError: %s' %
                        (ip, str(e)), 'error')
    except socket.timeout:
        output += color('Timeout exceeded connecting to device: %s\n' % ip,
                        'error')
    except socket.error:
        output += color('The device refused the connection on port %s' % port,
                        'error')
    else:
        # if there are no args to pass through
        if args is None:
            output += function(conn)
        # if we do have args to pass through
        else:
            output += function(conn, *args)
        # disconnect so sessions don't stay alive on the device.
        conn.disconnect()
    # no matter what happens, return the output
    return (output, no_highlight)


def commit(conn, cmds, commit_check, confirmed, commit_blank,
           comment, at_time, synchronize):
    """Execute a commit against the device.

    Purpose: This function will send set command(s) to a device, and commit
           | the change. It can be called by any function that needs to
           | commit or commit check.

    @param conn: This is the Jaide connection to the remote device.
    @type conn: jaide.Jaide object
    @param cmds: String containing the set command to be sent to the
               | device, or a list of strings of multiple set cmds. Either
               | way, the function will respond accordingly, and only one
               | commit will take place.
    @type cmds: str
    @param commit_check: A bool set to true if the user wants to only run a
                       | commit check, and not commit any changes.
    @type commit_check: bool
    @param confirmed: An integer of minutes that the user wants to
                         | commit confirm for.
    @type confirmed: int
    @param commit_blank: A bool set to true if the user wants to only make
                       | a blank commit.
    @type commit_blank: bool
    @param comment: A string that will be logged to the commit log
                  | describing the commit.
    @type comment: str
    @param at_time: A string containing the time or time and date of when
                  | the commit should happen. Junos is expecting one of two
                  | formats:
                  | A time value of the form hh:mm[:ss] (hours, minutes,
                  |     and optionally seconds)
                  | A date and time value of the form yyyy-mm-dd hh:mm[:ss]
                  |     (year, month, date, hours, minutes, and optionally
                  |      seconds)
    @type at_time: str
    @param synchronize: A bool set to true if the user wants to synchronize
                      | the commit across both REs.
    @type synchronize: bool

    @returns: The output that should be shown to the user.
    @rtype: str
    """
    output = ""
    # If they just want to validate the config, without committing
    if commit_check:
        try:
            results = conn.commit_check(cmds)
        except RPCError:
            output += color("\nUncommitted changes left on the device or "
                            "someone else is in edit mode, couldn't lock the "
                            "candidate configuration.\n", 'error')
        except:
            output += color("Failed to commit check on device %s for an "
                            "unknown reason." % ip, 'error')
        else:
            # add the 'show | compare' output.
            output += (color("Compare results:\n") + conn.compare_config(cmds)
                       + '\n')
            output += color("\nCommit check results from: %s\n" % conn.host)
            output += results
    # Actually commit the cmds.
    else:
        # add the 'show | compare' output.
        if not commit_blank:  # no results to show on blank commit.
            output += (color("Compare results:\n") + conn.compare_config(cmds)
                       + '\n')
        if confirmed:
            output += color("Attempting to commit confirm on device: %s\n"
                            % conn.host)
        else:
            output += color("Attempting to commit on device: %s\n\n" %
                            conn.host)
        try:
            output += conn.commit(confirmed=confirmed,
                                  comment=comment, at_time=at_time,
                                  synchronize=synchronize, commands=cmds)
        except RPCError as e:
            output += color('Commit could not be completed on this device, '
                            'due to the following error: \n' + str(e), 'error')
        else:
            if 'commit complete' in output:
                output = (output.split('commit complete')[0] +
                          color('Commit complete on device: ' +
                                conn.host + '\n'))
                if confirmed:
                    output += color('Commit confirm will rollback in %s '
                                    'minutes unless you commit again' %
                                    str(confirmed))
            elif 'commit at' in output:
                output = (output.split('commit at will be executed at')[0] +
                          color('Commit staged to happen at: %s' % at_time))
            else:
                if 'failed' in output:
                    output = output.replace('failed', color('failed', 'error'))
                if 'error' in output:
                    output = output.replace('error', color('error', 'error'))
                output += color('Commit Failed on device: ' + conn.host + '\n')
    return output


def copy_file(conn, direction, source, dest, multi, progress):
    """ SCP copy file(s) to or from the device.

    @param conn: The Jaide session object for the device
    @type conn: jaide.Jaide object
    @param direction: the direction of the copy, either 'push' or 'pull'
    @type direction: str
    @param source: the source filepath or dirpath
    @type source: str
    @param dest: the destination filepath or dirpath
    @type dest: str
    @param multi: bool set to True if we're copying from more than one device.
                | This determines the naming structure of received files/dirs.
    @type multi: bool
    @param progress: bool set to True if we should request a progress callback
                   | from the Jaide object. set to false on args.quiet, or when
                   | we're copying to/from multiple devices.
    @type progress: bool

    @returns: the output from the copy operation
    @rtype: str
    """
    output = "\n"
    # Source and destination filepath validation
    # Check if the destination ends in a '/', if not, we need to add it.
    dest = dest + '/' if dest[-1] != '/' else dest
    # If the source ends in a slash, we need to remove it. For copying
    # directories, this will ensure that the local directory gets created
    # remotely, and not just the contents. Basically, this forces the behavior
    # 'scp -r /var/log /dest/loc' instead of 'scp -r /var/log/* /dest/loc'
    source = source[:-1] if source[-1] == '/' else source
    # get just the source filename, in case we're pulling from multiple devices
    source_file = path.basename(source) if not '' else path.basename(path.join(source, '..'))
    if direction.lower() == 'pull':
        # try to create the local directory
        if '.' not in path.basename(dest):
            if not path.exists(dest):
                os.makedirs(dest)
        # name the file with the host if copying from multiple devices.
        dest_file = dest + conn.host + '_' + source_file if multi else dest + source_file
        output += ('Retrieving %s:%s, and putting it in %s\n' %
                   (conn.host, source, path.normpath(dest_file)))
        try:
            conn.scp_pull(source, dest_file, progress)
        except SCPException as e:
            return output + color('!!! Error during copy from ' + conn.host +
                                  '. Some files may have failed to transfer. '
                                  'SCP Module error:\n' + str(e) + ' !!!\n',
                                  'error')
        except (IOError, OSError) as e:
            return output + color('!!! The local filepath was not found! Note'
                                  ' that \'~\' cannot be used. Error:\n'
                                  + str(e) + ' !!!\n', 'error')
        else:
            output += color('Received %s:%s and stored it in %s.\n' %
                            (conn.host, source, path.normpath(dest_file)))
    elif direction.lower() == "push":
        source = path.normpath(source)
        output += ('Pushing %s to %s:%s\n' % (source, conn.host, dest))
        try:
            conn.scp_push(source, dest, progress)
        except SCPException as e:
            return output + color('!!! Error during copy from ' + conn.host +
                                  '. Some files may have failed to transfer. '
                                  'SCP Module error:\n' + str(e) + ' !!!\n',
                                  'error')
        except (IOError, OSError) as e:
            return output + color('!!! The local filepath was not found! Note'
                                  ' that \'~\' cannot be used. Error:\n'
                                  + str(e) + ' !!!\n', 'error')
        else:
            output += color('Pushed %s to %s:%s\n' % (source, conn.host, dest))
    if progress:
        print '\n'
    return output


def dev_info(conn):
    """Get basic device information."""
    return '\n' + conn.dev_info()


def diff_config(conn, second_host):
    """ Compare the configuration between two devices.

    @param conn: the Jaide connection for the first device.
    @type conn: jaide.Jaide object
    @param second_host: a list containing [0] the IP/hostname of the second
                      | device to pull from, and [1] the mode in which we are
                      | retrieving the config ('set' or 'stanza')
    @type second_host: list

    @returns: the config differences
    @rtype: str
    """
    try:
        # iterate over the diff lines between the two devices, merging them
        output = '\n'.join([diff for diff in
                            conn.diff_config(second_host[0],
                                             second_host[1].lower())])
    except errors.AuthenticationError:  # NCClient auth failure
        output = color('Authentication failed for device: %s\n' %
                       second_host[0], 'error')
    except AuthenticationException:  # Paramiko auth failure
        output = color('Authentication failed for device: %s\n' %
                       second_host[0], 'error')
    except SSHException as e:
        output = color('Error connecting to device: %s\nError: %s' %
                       (second_host[0], str(e)), 'error')
    except socket.timeout:
        output = color('Timeout exceeded connecting to device: %s\n' %
                       second_host[0], 'error')
    if output.strip() == '':
        output = color("There were no config differences between %s and %s\n" %
                       (conn.host, second_host[0]))
    else:
        # color removals as errors, and additions as success
        output = output.replace('---', color('---', 'error'))
        output = output.replace('+++', color('+++'))
        output = output.replace('\n-', color('\n-', 'error'))
        output = output.replace('\n+', color('\n+'))
        output = output.replace('@@', color('@@', 'info'))
    return output


def health_check(conn):
    """Get alarm and health information."""
    return '\n' + conn.health_check()


def int_errors(conn):
    """Get any interface errors from the device."""
    response = '\n' + conn.int_errors()
    if 'No interface errors' in response:
        response = color(response)
    else:
        response = color(response, 'error')
    return response


def multi_cmd(conn, commands, shell, req_format='text'):
    """ Execute a shell or operational mode command against the device.

    Purpose: This function will determine if we are trying to send multiple
           | commands to a device. It is used for operational mode commands
           | or shell commands. If we have more than one command to send,
           | then we need to use jaide.clean_lines() to clean them, getting
           | rid of comments and blank lines, and send them individually.
           | Otherwise, we just send the one command.

    @param conn: the connection to the remote device, which should be a
               | Jaide object.
    @type conn: jaide.Jaide
    @param commands: String containing one of these things:
                   | A single operational show or shell command.
                   | A comma separated string of commands.
                   | A python list of commands
                   | A filepath to a file with a command on each line.
    @type commands: str
    @param shell: boolean whether or not we are sending shell commands.
    @type shell: bool
    @param req_format: string specifying what format to request for the
                     | response from the device. Defaults to text, but
                     | also accepts xml.

    @returns: The output that should be shown to the user.
    @rtype: str
    """
    output = ""
    for cmd in clean_lines(commands):
        prompt = color('\n> ' + cmd, 'info')
        if shell:
            output += prompt + conn.shell_cmd(cmd)
        else:
            xpath_expr = ''
            # Get xpath expression from the command, if it is there.
            # If there is an xpath expr, the output will be xml,
            # overriding the req_format parameter
            #
            # Example command forcing xpath: show route % //rt-entry
            if len(cmd.split('%')) == 2:
                op_cmd = cmd.split('%')[0] + '\n'
                xpath_expr = cmd.split('%')[1].strip()
            if xpath_expr:
                output += (prompt +
                           conn.op_cmd(command=op_cmd, req_format='xml',
                                       xpath_expr=xpath_expr) + '\n')
            else:
                output += prompt + conn.op_cmd(cmd, req_format=req_format)
    return output


def write_to_file(output):
    """ Print the output to the user, or write it to file.

    Purpose: This function is called to either print the output to
           | the user, or write it to a file
           | if we've received a filepath prepended on the output string in
           | between identifiers '*****WRITE_TO_FILE*****'

    @param output: Two value tuple. the first is the output that we should be
                 | printing to the user, or writing to file. The second is the
                 | value of the no_highlight argument, to let us know if we
                 | should color the output to the user or not.
    @type output: (str, bool) tuple

    @returns: None
    """
    no_highlight = output[1]
    output = output[0]
    if "*****WRITE_TO_FILE*****" in output:
        screen_out = ""
        dest_file = output.split('*****WRITE_TO_FILE*****')[1]
        style = output.split('*****WRITE_TO_FILE*****')[2]
        # need to strip ANSI color codes from the string
        output = strip_color(output.split('*****WRITE_TO_FILE*****')[3])
        # open the output file if one was specified.
        if style.lower() in ["s", "single"]:
            try:
                out_file = open(dest_file, 'a+b')
            except IOError as e:
                screen_out += (color('Error opening output file \'%s\' for '
                                     'writing. Here is the output that '
                                     'would\'ve been written:\n' % dest_file,
                                     'error'))
                screen_out += output
                screen_out += (color('\n\nHere is the error for opening the '
                                     'output file:' + str(e), 'error'))
            else:
                out_file.write('%s\n\n' % output)
                screen_out += (color('\nOutput written/appended to: ' +
                                     dest_file))
        elif style.lower() in ["m", "multiple"]:
            # get the ip for the current device from the output.
            ip = output.split('device: ')[1].split('\n')[0].strip()
            try:
                filepath = path.join(path.split(dest_file)[0], ip + "_" +
                                     path.split(dest_file)[1])
                out_file = open(filepath, 'a+b')
            except IOError as e:
                screen_out += (color('Error opening output file \'%s\' for '
                                     'writing. Here is the output that '
                                     'would\'ve been written:\n' % dest_file,
                                     'error'))
                screen_out += output
                screen_out += (color('\n\nHere is the error for opening the '
                                     'output file:' + str(e), 'error'))
            else:
                out_file.write(output)
                screen_out += color('\nOutput appended to: ' + filepath)
                out_file.close()
        if no_highlight:
            screen_out = strip_color(screen_out)
        print screen_out
    else:
        if no_highlight:
            output = strip_color(output)
        # --scp function copy_file will return '' if we aren't writing to a
        # file, because the output is printed to the user immediately.
        # Therefore we only need to print if something exists.
        print output if output else None


def main():
    """ Execute the script, and perform the appropriate function.

    Purpose: This function handles all argument parsing and validation,
           | along with mapping the argument they used with the correct
           | function. A pool is spawned for running the function they
           | need.
    """
    args = prs.parse_args()
    # Correlates argument with function pointer
    function_translation = {
        "command": multi_cmd,
        "commit_blank": commit,
        "diff_config": diff_config,
        "health_check": health_check,
        "info": dev_info,
        "int_error": int_errors,
        "make_commit": commit,
        "scp": copy_file,
        "shell": multi_cmd
    }
    # Correlates which params need to be passed through open_connection() to
    # the final function.
    args_translation = {
        "command": [args.command, False, args.format.lower()],
        "commit_blank":
            [args.make_commit, args.commit_check, args.confirmed,
                args.commit_blank, args.commit_comment, args.commit_at,
                args.commit_synchronize],
        "diff_config": [args.diff_config],
        "health_check": None,
        "info": None,
        "int_error": None,
        "make_commit":
            [args.make_commit, args.commit_check, args.confirmed,
                args.commit_blank, args.commit_comment, args.commit_at,
                args.commit_synchronize],
        "shell": [args.shell, True, args.sess_timeout]
    }

    # Verify requirements.
    if args.diff_config:
        if args.diff_config[1].lower() not in ['set', 'stanza']:
            prs.error(color("When using the -d/--diff flag, you must specify "
                            "two arguments, the second host and the mode, "
                            "either set or stanza. For example: '-d "
                            "10.0.0.10 set'", 'error'))
    if args.scp:
        if (args.scp[0].lower() not in ['pull', 'push']):
            prs.error(color('When using the --scp flag, you must specify the '
                      'direction as the first argument. For example: "--scp '
                            'pull /var/tmp /path/to/local/folder"', 'error'))
        args_translation["scp"] = [args.scp[0], args.scp[1], args.scp[2],
                                   False, True]

    # if they are doing commit_at, ensure the input is formatted correctly.
    if args.commit_at:
        if (re.search(r'([0-2]\d)(:[0-5]\d){1,2}', args.commit_at) is None and
            re.search(r'\d{4}-[01]\d-[0-3]\d [0-2]\d:[0-5]\d(:[0-5]\d)?',
                      args.commit_at) is None):
            raise BaseException("The specified commit at time is not in one of"
                                "the two following formats:\nA time value of "
                                "the form 'hh:mm[:ss]'\nA date and time value "
                                "of the form 'yyyy-mm-dd hh:mm[:ss]' (seconds "
                                "are optional).")

    # Check if the username and password are the defaults.
    # If they are, we'll prompt the user for them.
    if args.username == 'default':
        args.username = raw_input("Username: ")
    if args.password == 'default':
        # getpass will not echo back to the user, for safe password entry.
        args.password = getpass.getpass()

    # Compares args to function_translation to figure out which we are doing
    # then looks up the function pointer and arguments
    # vars(args) will convert the Namespace from argparser in to a dictionary
    # we can iterate over
    for key in vars(args).keys():
        if key in function_translation:
            if vars(args)[key] not in [None, False]:
                function = function_translation[key]
                argsToPass = args_translation[key]

    # build ip list so we can know if we're hitting multiple devices
    # which is needed for the scp function to know when to output to the user
    # immediately, and when to suppress progress updates.
    ip_list = [ip for ip in clean_lines(args.ip)]
    if function == copy_file:
        # set 'multi' param to true if scp'ing to more than one device
        argsToPass[-2] = True if len(ip_list) > 1 else False
        # set progress callback to false if quiet mode
        argsToPass[-1] = False if args.quiet or len(ip_list) > 1 else True
    if args.diff_config and len(ip_list) != 1:
        prs.error(color('When trying to do a config diff, you must specify one'
                        ' IP/host in the -i argument, and on in the -d '
                        'argument', 'error'))
    # use a multiprocessing pool if multiple devices.
    if len(ip_list) > 1:
        # Use # of CPU cores * 2 threads. Cpu_count usually returns double the
        # number of physical cores because of hyperthreading.
        mp_pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
        for ip in ip_list:
            mp_pool.apply_async(open_connection,
                                args=(ip.strip(), args.username, args.password,
                                      function, argsToPass, args.write,
                                      args.conn_timeout, args.sess_timeout,
                                      args.port, args.no_highlight),
                                callback=write_to_file)
        mp_pool.close()
        mp_pool.join()
    else:  # no need for mp_pool when just hitting one device.
        write_to_file(open_connection(ip.strip(), args.username, args.password,
                                      function, argsToPass, args.write,
                                      args.conn_timeout, args.sess_timeout,
                                      args.port, args.no_highlight))

if __name__ == '__main__':
    main()
