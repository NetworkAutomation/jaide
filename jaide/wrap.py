#!/usr/bin/env python
""" Jaide CLI script for manipulating Junos devices.

This is a wrapper for the Jaide class that provides mostly error handling.
For example, command errors, auth errors, unreachable devices, etc are
returned as strings. Instead of raising exceptions, this help other tools
(in our case the CLI tool and JGUI) offer a more user-friendly experience.

For expansive information on the Jaide class and the Jaide CLI tool,
refer to the readme file or the associated examples/documentation. More
information can be found at the github page:

https://github.com/NetworkAutomation/jaide
"""
# standard modules
from os import path
import socket
import lxml
# intra-Jaide imports
from core import Jaide
from utils import clean_lines
from color_utils import color, color_diffs
# The rest are non-standard modules:
from ncclient.transport import errors
from ncclient.operations.rpc import RPCError
from paramiko import SSHException, AuthenticationException
from scp import SCPException
import click


# TODO: make this a decorator function, handing the Jaide object downstream?
def open_connection(ip, username, password, function, args, write=False,
                    conn_timeout=5, sess_timeout=300, port=22):
    """ Open a Jaide session with the device.

    To open a Jaide session to the device, and run the appropriate function
    against the device. Arguments for the downstream function are passed
    through.

    @param ip: String of the IP or hostname of the device to connect to.
    @type ip: str
    @param username: The string username used to connect to the device.
    @type useranme: str
    @param password: The string password used to connect to the device.
    @type password: str
    @param function: The downstream jaide.wrap function we'll be handing
                   | off the jaide.Jaide() object to execute the command
                   | once we've established the connection.
    @type function: function pointer.
    @param args: The arguments that we will hand off to the downstream
               | function.
    @type args: list
    @param write: If set, it would be a tuple that we pass back as part of
                | our return statement, so that any callback function
                | can know how and where to put the output from the device.
    @type write: False or tuple.
    @param conn_timeout: Sets the connection timeout value. This is how
                       | we'll wait when connecting before classifying
                       | the device unreachable.
    @type conn_timeout: int
    @param sess_timeout: Sets the session timeout value. A higher value may
                       | be desired for long running commands, such as
                       | 'request system snapshot slice alternate'
    @type sess_timeout: int
    @param port: The port to connect to the device on. Defaults to 22.
    @type port: int

    @returns: We could return either just a string of the output from the
            | device, or a tuple containing the information needed to write
            | to a file and the string output from the device.
    @rtype: Tuple or str
    """
    # start with the header line on the output.
    output = color('=' * 50 + '\nResults from device: %s\n' % ip, 'yel')
    try:
        # create the Jaide session object for the device.
        conn = Jaide(ip, username, password, connect_timeout=conn_timeout,
                     session_timeout=sess_timeout, port=port)
        if write is not False:
            return write, output + function(conn, *args)
        else:
            return output + function(conn, *args)
    except errors.SSHError:
        output += color('Unable to connect to port %s on device: %s\n' %
                        (str(port), ip), 'red')
    except errors.AuthenticationError:  # NCClient auth failure
        output += color('Authentication failed for device: %s' % ip, 'red')
    except AuthenticationException:  # Paramiko auth failure
        output += color('Authentication failed for device: %s' % ip, 'red')
    except SSHException as e:
        output += color('Error connecting to device: %s\nError: %s' %
                        (ip, str(e)), 'red')
    except socket.timeout:
        output += color('Timeout exceeded connecting to device: %s' % ip, 'red')
    except socket.gaierror:
        output += color('No route to host, or invalid hostname: %s' % ip, 'red')
    except socket.error:
        output += color('The device refused the connection on port %s, or '
                        'no route to host.' % port, 'red')
    if write is not False:
        return write, output
    else:
        return output


def command(jaide, commands, format="text", xpath=False):
    """ Run an operational command.

    @param jaide: The jaide connection to the device.
    @type jaide: jaide.Jaide object
    @param commands: the operational commands to send to the device.
    @type commands: str or list
    @param format: The desired output format from the device, either 'text'
                 | or 'xml' is supported.
    @type format: str
    @param xpath: The xpath expression to filter the results from the device.
                | If set, this forces the output to be requested in xml format.
    @type xpath: str

    @returns: The output from the device, and xpath filtered if desired.
    @rtype: str
    """
    output = ""
    for cmd in clean_lines(commands):
        expression = ""
        output += color('> ' + cmd + '\n', 'yel')
        # Get xpath expression from the command, if it is there.
        # If there is an xpath expr, the output will be xml,
        # overriding the req_format parameter
        #
        # Example command forcing xpath: show route % //rt-entry
        if len(cmd.split('%')) == 2:
            expression = cmd.split('%')[1].strip()
            cmd = cmd.split('%')[0] + '\n'
        elif xpath is not False:
            expression = xpath
        if expression:
            try:
                output += jaide.op_cmd(command=cmd, req_format='xml',
                                       xpath_expr=expression) + '\n'
            except lxml.etree.XMLSyntaxError:
                output += color('Xpath expression resulted in no response.\n',
                                'red')
        else:
            output += jaide.op_cmd(cmd, req_format=format) + '\n'
    return output


def commit(jaide, commands, check, sync, comment, confirm, at_time, blank):
    """ Execute a commit against the device.

    Purpose: This function will send set commands to a device, and commit
           | the changes. Options exist for confirming, comments,
           | synchronizing, checking, blank commits, or delaying to a later
           | time/date.

    @param jaide: The jaide connection to the device.
    @type jaide: jaide.Jaide object
    @param commands: String containing the set command to be sent to the
                   | device. It can be a python list of strings, a single set
                   | command, a comma separated string of commands, or a
                   | string filepath pointing to a file with set commands
                   | on each line.
    @type commands: str or list
    @param check: A bool set to true to only run a commit check, and not
                | commit any changes. Useful for checking syntax of set
                | commands.
    @type check: bool
    @param sync: A bool set to true to sync the commit across both REs.
    @type sync: bool
    @param comment: A string that will be logged to the commit log
                  | describing the commit.
    @type comment: str
    @param confirm: An integer of seconds to commit confirm for.
    @type confirm: int
    @param at_time: A string containing the time or time and date of when
                  | the commit should happen. Junos is expecting one of two
                  | formats:
                  | A time value of the form hh:mm[:ss] (hours, minutes,
                  |     and optionally seconds)
                  | A date and time value of the form yyyy-mm-dd hh:mm[:ss]
                  |     (year, month, date, hours, minutes, and optionally
                  |      seconds)
    @type at_time: str
    @param blank: A bool set to true to only make a blank commit. A blank
                | commit makes a commit, but doesn't have any set commands
                | associated with it, so no changes are made, but a commit
                | does happen.
    @type blank: bool

    @returns: The output from the device.
    @rtype: str
    """
    # set the commands to do nothing if the user wants a blank commit.
    if blank:
        commands = 'annotate system ""'
    output = ""
    # add show | compare output
    if commands != "":
        output += color("show | compare:\n", 'yel')
        try:
            output += color_diffs(jaide.compare_config(commands)) + '\n'
        except RPCError as e:
            output += color("Could not get config comparison results before"
                            " committing due to the following error:\n%s" %
                            str(e))
    # If they just want to validate the config, without committing
    if check:
        output += color("Commit check results from: %s\n" % jaide.host, 'yel')
        try:
            output += jaide.commit_check(commands) + '\n'
        except RPCError:
            output += color("Uncommitted changes left on the device or someone"
                            " else is in edit mode, couldn't lock the "
                            "candidate configuration.\n", 'red')
        except:
            output += color("Failed to commit check on device %s for an "
                            "unknown reason.\n" % jaide.host, 'red')
    # Actually make a commit
    else:
        output += color("Attempting to commit on device: %s\n" % jaide.host,
                        'yel')
        try:
            results = jaide.commit(confirmed=confirm, comment=comment,
                                   at_time=at_time, synchronize=sync,
                                   commands=commands)
        except RPCError as e:
            output += color('Commit could not be completed on this device, due'
                            ' to the following error(s):\n' + str(e), 'red')
        # Jaide command succeeded, parse results
        else:
            if 'commit complete' in results:
                output += results.split('commit complete')[0] + '\n'
                output += color('Commit complete on device: %s\n' % jaide.host)
                if confirm:
                    output += color('Commit confirm will rollback in %s '
                                    'minutes unless you commit again.\n' %
                                    str(confirm/60))
            elif 'commit at' in results:
                output += results.split('commit at will be executed at')[0]
                output += color('Commit staged to happen at: %s\n' % at_time)
            else:
                if 'failed' in results:
                    output += (results.replace('failed', color('failed',
                               'red')))
                if 'red' in results:
                    output += (results.replace('red', color('red',
                               'red')))
                output += color('Commit Failed on device: %s\n' % jaide.host,
                                'red')
    return output


def compare(jaide, commands):
    """ Perform a show | compare with some set commands.

    @param jaide: The jaide connection to the device.
    @type jaide: jaide.Jaide object
    @param commands: The set commands to send to the device to compare with.
    @type commands: str or list

    @returns: The output from the device.
    @rtype str
    """
    output = color("show | compare:\n", 'yel')
    return output + color_diffs(jaide.compare_config(commands))


def device_info(jaide):
    """ Retrieve basic device information.

    @param jaide: The jaide connection to the device.
    @type jaide: jaide.Jaide object

    @returns: The output from the device.
    @rtype str
    """
    return jaide.device_info()


def diff_config(jaide, second_host, mode):
    """ Perform a show | compare with some set commands.

    @param jaide: The jaide connection to the device.
    @type jaide: jaide.Jaide object
    @param second_host: The device IP or hostname of the second host to
                      | compare with.
    @type second_host: str
    @param mode: How to compare the configuration, either in 'set' mode or
               | 'stanza' mode.
    @type mode: str

    @returns: The comparison between the two devices.
    @rtype str
    """
    try:
        # create a list of all the lines that differ, and merge it.
        output = '\n'.join([diff for diff in
                            jaide.diff_config(second_host, mode.lower())])
    except errors.SSHError:
        output = color('Unable to connect to port %s on device: %s\n' %
                       (str(jaide.port), second_host), 'red')
    except errors.AuthenticationError:  # NCClient auth failure
        output = color('Authentication failed for device: %s' %
                       second_host, 'red')
    except AuthenticationException:  # Paramiko auth failure
        output = color('Authentication failed for device: %s' %
                       second_host, 'red')
    except SSHException as e:
        output = color('Error connecting to device: %s\nError: %s' %
                       (second_host, str(e)), 'red')
    except socket.timeout:
        output = color('Timeout exceeded connecting to device: %s' %
                       second_host, 'red')
    except socket.gaierror:
        output = color('No route to host, or invalid hostname: %s' %
                       second_host, 'red')
    except socket.error:
        output = color('The device refused the connection on port %s, or '
                       'no route to host.' % jaide.port, 'red')
    if output.strip() == '':
        output = color("There were no config differences between %s and %s\n" %
                       (jaide.host, second_host), 'yel')
    else:
        # color removals red, and additions green
        return color_diffs(output)
    return output


def health_check(jaide):
    """ Retrieve alarm, CPU, RAM, and temperature status.

    @param jaide: The jaide connection to the device.
    @type jaide: jaide.Jaide object

    @returns: The output from the device.
    @rtype str
    """
    return jaide.health_check()


def interface_errors(jaide):
    """ Retrieve any interface errors from all interfaces on a device.

    @param jaide: The jaide connection to the device.
    @type jaide: jaide.Jaide object

    @returns: The output from the device.
    @rtype str
    """
    response = jaide.interface_errors()
    if 'No interface errors' in response:
        return response
    else:
        return color(response, 'red')


def pull(jaide, source, destination, progress, multi):
    """ Copy file(s) from a device to the local machine.

    @param jaide: The jaide connection to the device.
    @type jaide: jaide.Jaide object
    @param source: The source filepath on the junos device to pull.
    @type source: str
    @param destination: the destination filepath on the local device for
                      | the files.
    @type destination: str
    @param progress: Flagged to True if the user desires to see the status
                   | as the copy happens.
    @type progress: bool
    @param multi: Flagged to true if we're copying from multiple devices.
                | Used to name the destination files.
    @type multi: bool

    @returns: The output of the copy.
    @rtype str
    """
    output = color('Retrieving %s:%s, and putting it in %s\n' %
                   (jaide.host, source, path.normpath(destination)), 'yel')
    # Check if the destination ends in a '/', if not, we need to add it.
    destination = destination + '/' if destination[-1] != '/' else destination
    # If the source ends in a slash, we need to remove it. For copying
    # directories, this will ensure that the local directory gets created
    # remotely, and not just the contents. Basically, this forces the behavior
    # 'scp -r /var/log /dest/loc' instead of 'scp -r /var/log/* /dest/loc'
    source = source[:-1] if source[-1] == '/' else source
    source_file = path.basename(source) if not '' else path.basename(path.join(source, '..'))
    dest_file = destination + jaide.host + '_' + source_file if multi else destination + source_file
    try:
        jaide.scp_pull(source, dest_file, progress)
        if progress:  # move to the next line if we were printing the progress
            click.echo('')
    except SCPException as e:
        output += color('!!! Error during copy from ' + jaide.host +
                        '. Some files may have failed to transfer. SCP Module'
                        ' error:\n' + str(e) + ' !!!\n', 'red')
    except (IOError, OSError) as e:
        output += color('!!! The local filepath was not found! Note that \'~\''
                        ' cannot be used. Error:\n' + str(e) + ' !!!\n',
                        'red')
    else:
        output += color('Received %s:%s and stored it in %s.\n' %
                        (jaide.host, source, path.normpath(dest_file)))
    return output


# TODO: multi not needed here at all?
def push(jaide, source, destination, progress, multi=False):
    """ Copy file(s) from the local machine to a junos device.

    @param jaide: The jaide connection to the device.
    @type jaide: jaide.Jaide object
    @param source: The source filepath on the junos device to pull.
    @type source: str
    @param destination: the destination filepath on the local device for
                      | the files.
    @type destination: str
    @param progress: Flagged to True if the user desires to see the status
                   | as the copy happens.
    @type progress: bool
    @param multi: Flagged to true if we're copying from multiple devices.
                | Not needed in this function
    @type multi: bool

    @returns: The output of the copy.
    @rtype str
    """
    output = color('Pushing %s to %s:%s\n' % (source, jaide.host, destination),
                   'yel')
    # Check if the destination ends in a '/', if not, we need to add it.
    destination = destination + '/' if destination[-1] != '/' else destination
    # If the source ends in a slash, we need to remove it. For copying
    # directories, this will ensure that the local directory gets created
    # remotely, and not just the contents. Basically, this forces the behavior
    # 'scp -r /var/log /dest/loc' instead of 'scp -r /var/log/* /dest/loc'
    source = source[:-1] if source[-1] == '/' else source
    try:
        jaide.scp_push(source, destination, progress)
        if progress:
            click.echo('')
    except SCPException as e:
        output += color('!!! Error during copy from ' + jaide.host +
                        '. Some files may have failed to transfer. SCP Module'
                        ' error:\n' + str(e) + ' !!!\n', 'red')
    except (IOError, OSError) as e:
        output += color('!!! The local filepath was not found! Note that \'~\''
                        ' cannot be used. Error:\n' + str(e) + ' !!!\n',
                        'red')
    else:
        output += color('Pushed %s to %s:%s\n' % (source, jaide.host,
                        destination))
    return output


def shell(jaide, commands):
    """ Send shell commands to a device.

    @param jaide: The jaide connection to the device.
    @type jaide: jaide.Jaide object
    @param commands: The shell commands to send to the device.
    @type commands: str or list.

    @returns: The output of the commands.
    @rtype str
    """
    out = ""
    for cmd in clean_lines(commands):
        out += color('> %s\n' % cmd, 'yel')
        out += jaide.shell_cmd(cmd) + '\n'
    return out
