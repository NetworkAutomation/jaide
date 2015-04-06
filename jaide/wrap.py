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


# TODO: Add color coding enhancement to github.
# TODO: Add separating CLI from Jaide Class enhancement to github.
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
    @param conn_timeout: Sets the connection timeout value. This is how
                       | we'll wait when connecting before classifying
                       | the device unreachable.
    @type conn_timeout: int
    @param sess_timeout: Sets the session timeout value. A higher value may
                       | be desired for long running commands, such as
                       | 'request system snapshot slice alternate'
    @type sess_timeout: int

    @returns: a tuple of the output of the jaide command being run, and a
            | boolean whether the output is to be highlighted or not.
    @rtype: (str, bool) tuple
    """
    # start with the header line on the output.
    output = color('=' * 50 + '\nResults from device: %s\n' % ip, 'info')
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
                        (str(port), ip), 'error')
    except errors.AuthenticationError:  # NCClient auth failure
        output += color('Authentication failed for device: %s' % ip, 'error')
    except AuthenticationException:  # Paramiko auth failure
        output += color('Authentication failed for device: %s' % ip, 'error')
    except SSHException as e:
        output += color('Error connecting to device: %s\nError: %s' %
                        (ip, str(e)), 'error')
    except socket.timeout:
        output += color('Timeout exceeded connecting to device: %s' % ip, 'error')
    except socket.gaierror:
        output += color('No route to host, or invalid hostname: %s' % ip, 'error')
    except socket.error:
        output += color('The device refused the connection on port %s, or '
                        'no route to host.' % port, 'error')
    if write is not False:
        return write, output
    else:
        return output


def command(jaide, commands, format="text", xpath=False):
    output = ""
    for cmd in clean_lines(commands):
        expression = ""
        output += color('> ' + cmd + '\n', 'info')
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
                                'error')
        else:
            output += jaide.op_cmd(cmd, req_format=format) + '\n'
    return output


def commit(jaide, commands, check, sync, comment, confirm, at_time, blank):
    # set the commands to do nothing if the user wants a blank commit.
    if blank:
        commands = 'annotate system ""'
    output = ""
    # add show | compare output
    if commands != "" and not blank:
        output += color("show | compare:\n", 'info')
        try:
            output += color_diffs(jaide.compare_config(commands)) + '\n'
        except RPCError as e:
            output += color("Could not get config comparison results before"
                            " committing due to the following error:\n%s" %
                            str(e))
    # If they just want to validate the config, without committing
    if check:
        output += color("Commit check results from: %s\n" % jaide.host, 'info')
        try:
            output += jaide.commit_check(commands) + '\n'
        except RPCError:
            output += color("Uncommitted changes left on the device or someone"
                            " else is in edit mode, couldn't lock the "
                            "candidate configuration.\n", 'error')
        except:
            output += color("Failed to commit check on device %s for an "
                            "unknown reason.\n" % jaide.host, 'error')
    # Actually make a commit
    else:
        output += color("Attempting to commit on device: %s\n" % jaide.host,
                        'info')
        try:
            results = jaide.commit(confirmed=confirm, comment=comment,
                                   at_time=at_time, synchronize=sync,
                                   commands=commands)
        except RPCError as e:
            output += color('Commit could not be completed on this device, due'
                            ' to the following error(s):\n' + str(e), 'error')
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
                               'error')))
                if 'error' in results:
                    output += (results.replace('error', color('error',
                               'error')))
                output += color('Commit Failed on device: %s\n' % jaide.host,
                                'error')
    return output


def compare(jaide, commands):
    output = color("show | compare:\n", 'info')
    return output + color_diffs(jaide.compare_config(commands))


def device_info(jaide):
    return jaide.device_info()


def diff_config(jaide, second_host, mode):
    try:
        # create a list of all the lines that differ, and merge it.
        output = '\n'.join([diff for diff in
                            jaide.diff_config(second_host, mode.lower())])
    except errors.SSHError:
        output = color('Unable to connect to port %s on device: %s\n' %
                       (str(jaide.port), second_host), 'error')
    except errors.AuthenticationError:  # NCClient auth failure
        output = color('Authentication failed for device: %s' %
                       second_host, 'error')
    except AuthenticationException:  # Paramiko auth failure
        output = color('Authentication failed for device: %s' %
                       second_host, 'error')
    except SSHException as e:
        output = color('Error connecting to device: %s\nError: %s' %
                       (second_host, str(e)), 'error')
    except socket.timeout:
        output = color('Timeout exceeded connecting to device: %s' %
                       second_host, 'error')
    except socket.gaierror:
        output = color('No route to host, or invalid hostname: %s' %
                       second_host, 'error')
    except socket.error:
        output = color('The device refused the connection on port %s, or '
                       'no route to host.' % jaide.port, 'error')
    if output.strip() == '':
        output = color("There were no config differences between %s and %s\n" %
                       (jaide.host, second_host), 'info')
    else:
        # color removals as errors, and additions as success
        return color_diffs(output)
    return output


def health_check(jaide):
    return jaide.health_check()


def interface_errors(jaide):
    response = jaide.interface_errors()
    if 'No interface errors' in response:
        return response
    else:
        return color(response, 'error')


def pull(jaide, source, destination, progress, multi):
    output = color('Retrieving %s:%s, and putting it in %s\n' %
                   (jaide.host, source, path.normpath(destination)), 'info')
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
                        ' error:\n' + str(e) + ' !!!\n', 'error')
    except (IOError, OSError) as e:
        output += color('!!! The local filepath was not found! Note that \'~\''
                        ' cannot be used. Error:\n' + str(e) + ' !!!\n',
                        'error')
    else:
        output += color('Received %s:%s and stored it in %s.\n' %
                        (jaide.host, source, path.normpath(dest_file)))
    return output


def push(jaide, source, destination, progress, multi=False):
    output = color('Pushing %s to %s:%s\n' % (source, jaide.host, destination),
                   'info')
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
                        ' error:\n' + str(e) + ' !!!\n', 'error')
    except (IOError, OSError) as e:
        output += color('!!! The local filepath was not found! Note that \'~\''
                        ' cannot be used. Error:\n' + str(e) + ' !!!\n',
                        'error')
    else:
        output += color('Pushed %s to %s:%s\n' % (source, jaide.host,
                        destination))
    return output


def shell(jaide, commands):
    out = ""
    for cmd in clean_lines(commands):
        out += color('> %s\n' % cmd, 'info')
        out += jaide.shell_cmd(cmd) + '\n'
    return out
