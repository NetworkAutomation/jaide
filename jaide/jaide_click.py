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
import lxml
# intra-Jaide imports
from core import Jaide
from utils import clean_lines
from color_utils import color, strip_color, secho
# The rest are non-standard modules:
from ncclient.transport import errors
from ncclient.operations.rpc import RPCError
from paramiko import SSHException, AuthenticationException
from scp import SCPException
import click
from functools import update_wrapper

# needed for '-h' to be a help option
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

# TODO: --compare argument for doing just comparison without commit checking.
# TODO: use 'click' instead of argparse?
# TODO: Verbosity argument for seeing more/less output?
# TODO: related to above, maybe change --quiet to show nothing?


@click.pass_context
def write_to_file(ctx, param, value):
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
    if value != ("default", "default"):
        # Validate the -w option
        try:
            mode, dest_file = (value[0], value[1])
        except IndexError:
            raise click.BadParameter('Expecting two arguments, one for how to '
                                     'output (s, single, m, multiple), and '
                                     'the second is a filepath where to put'
                                     ' the output.')
        if mode.lower() not in ['s', 'single', 'm', 'multiple']:
            raise click.BadParameter('The first argument of the -w/--write '
                                     'option must specifies whether to write'
                                     ' to one file per device, or all device'
                                     ' output to a single file. Valid options'
                                     ' are "s", "single", "m", and "multiple"')
        # TODO: currently forcing 's' output mode, can't write to multiple.
        try:
            ctx.obj['out'] = open(dest_file, 'a+b')
        except IOError as e:
            secho('Error opening output file: %s\nWill move forward printing '
                  'to terminal instead.' % str(e), 'error')
            ctx.obj['out'] = sys.stdout
    else:
        ctx.obj['out'] = sys.stdout
    # if "*****WRITE_TO_FILE*****" in output:
    #     screen_out = ""
    #     dest_file = output.split('*****WRITE_TO_FILE*****')[1]
    #     style = output.split('*****WRITE_TO_FILE*****')[2]
    #     # need to strip ANSI color codes from the string
    #     output = strip_color(output.split('*****WRITE_TO_FILE*****')[3])
    #     # open the output file if one was specified.
    #     if style.lower() in ["s", "single"]:
    #         try:
    #             out_file = open(dest_file, 'a+b')
    #         except IOError as e:
    #             screen_out += (color('Error opening output file \'%s\' for '
    #                                  'writing. Here is the output that '
    #                                  'would\'ve been written:\n' % dest_file,
    #                                  'error'))
    #             screen_out += output
    #             screen_out += (color('\n\nHere is the error for opening the '
    #                                  'output file:' + str(e), 'error'))
    #         else:
    #             out_file.write('%s\n\n' % output)
    #             screen_out += (color('\nOutput written/appended to: ' +
    #                                  dest_file))
    #     elif style.lower() in ["m", "multiple"]:
    #         # get the ip for the current device from the output.
    #         ip = output.split('device: ')[1].split('\n')[0].strip()
    #         try:
    #             filepath = path.join(path.split(dest_file)[0], ip + "_" +
    #                                  path.split(dest_file)[1])
    #             out_file = open(filepath, 'a+b')
    #         except IOError as e:
    #             screen_out += (color('Error opening output file \'%s\' for '
    #                                  'writing. Here is the output that '
    #                                  'would\'ve been written:\n' % dest_file,
    #                                  'error'))
    #             screen_out += output
    #             screen_out += (color('\n\nHere is the error for opening the '
    #                                  'output file:' + str(e), 'error'))
    #         else:
    #             out_file.write(output)
    #             screen_out += color('\nOutput appended to: ' + filepath)
    #             out_file.close()
    #     if no_highlight:
    #         screen_out = strip_color(screen_out)
    #     print screen_out
    # else:
    #     if no_highlight:
    #         output = strip_color(output)
    #     # --scp function copy_file will return '' if we aren't writing to a
    #     # file, because the output is printed to the user immediately.
    #     # Therefore we only need to print if something exists.
    #     print output if output else None


# TODO: can't change the name of prog from jaide_click.py in help text using click?
@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('-i', '--ip', 'host', prompt="IP or hostname of Junos device",
              help="The target hostname(s) or IP(s). Can be a comma separated"
              " list, or path to a file listing devices on individual lines.")
@click.option('-u', '--username', prompt="Username")
@click.password_option('-p', '--password', prompt="Password")
@click.option('-P', '--port', default=22, help="The port to connect to. "
              "Defaults to SSH (22)")
@click.option('-t', '--session-timeout', type=click.IntRange(5, 7200),
              default=300, help="The session timeout value, in seconds, for"
              " declaring a lost session. Default is 300 seconds. This should"
              " be increased when no output could be seen for more than 5 "
              "minutes (ex. requesting a system snapshot).")
@click.option('-T', '--connect-timeout', type=click.IntRange(1, 60), default=5,
              help="The timeout, in seconds, for declaring a device "
              "unreachable during connection establishment. Default is 5"
              " seconds.")
@click.version_option(version='2.0.0', prog_name='jaide')
@click.option('-w', '--write', nargs=2, type=click.STRING, expose_value=False,
              callback=write_to_file, help="Write the output to a file "
              "instead of echoing it to the terminal. This can be useful "
              "when touching more than one device, because the output can be "
              "split into a file per device. In this case, output filename "
              "format is IP_FILENAME.", metavar="[s | single | m | multiple]"
              " FILEPATH", default=("default", "default"))
@click.pass_context
def main(ctx, host, password, port, session_timeout, connect_timeout,
         username):
    """ Manipulate one or more Junos devices.

    Will connect to one or more Junos devices, and manipulate them based on
    the command you have chosen. If a comma separated list or a file
    containing IP/hostnames on each line is given for the IP option, the
    commands will be carried out simultaneously to each device.
    """
    function_translation = {
        "command": command
    }
    # grab all the IPs
    ip_list = [ip for ip in clean_lines(host)]
    if len(ip_list) > 1:
        mp_pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
        ctx.obj['hosts'] = {}
        for ip in ip_list:
            print ip
            ctx.obj['hosts'][ip] = open_connection(ctx, ip, username, password,
                                                   connect_timeout,
                                                   session_timeout, port)
            mp_pool.apply_async(function_translation[ctx.invoked_subcommand],
                                args=(ctx.args[1:]))
        mp_pool.close()
        mp_pool.join()
    else:
        ctx.obj['jaide'] = open_connection(ctx, host, username, password,
                                           connect_timeout, session_timeout,
                                           port)


def generator(f):
    """Similar to the :func:`processor` but passes through old values
    unchanged and does not pass through the values as parameter.
    """
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        for conn in ctx.obj['hosts']:
            yield ctx.invoke(f, conn, *args, **kwargs)
        # for item in f(*args, **kwargs):
        #     yield item
    return update_wrapper(new_func, f)


def open_connection(ctx, ip, username, password, conn_timeout=5,
                    sess_timeout=300, port=22):
    """ Open a Jaide session with the device.

    Purpose: To open a Jaide session to the device, and run the
           | appropriate function against the device.

    @param ip: String of the IP of the device, to open the connection
    @type ip: str or unicode
    @param username: The string username used to connect to the device.
    @type useranme: str or unicode
    @param password: The string password used to connect to the device.
    @type password: str or unicode
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
    # TODO: if failed to connect, need to stop from moving to the command, thinking a decorator function around the other commands that checks for ctx.obj['jaide'] is None
    # start with the header line on the output.
    secho('=' * 50 + '\nResults from device: %s\n' % ip, 'info',
          file=ctx.obj['out'])
    try:
        # create the Jaide session object for the device.
        conn = Jaide(ip, username, password, connect_timeout=conn_timeout,
                     session_timeout=sess_timeout, port=port)
    except errors.SSHError:
        secho('Unable to connect to port %s on device: %s\n' %
              (str(port), ip), 'error',
              file=ctx.obj['out'])
    except errors.AuthenticationError:  # NCClient auth failure
        secho('Authentication failed for device: %s\n' % ip, 'error',
              file=ctx.obj['out'])
    except AuthenticationException:  # Paramiko auth failure
        secho('Authentication failed for device: %s\n' % ip, 'error',
              file=ctx.obj['out'])
    except SSHException as e:
        secho('Error connecting to device: %s\nError: %s' %
              (ip, str(e)), 'error', file=ctx.obj['out'])
    except socket.timeout:
        secho('Timeout exceeded connecting to device: %s\n' % ip, 'error',
              file=ctx.obj['out'])
    except socket.error:
        secho('The device refused the connection on port %s' % port, 'error',
              file=ctx.obj['out'])
    else:
        return conn


def at_time_validate(ctx, param, value):
    """ Callback validating the at_time commit option. """
    # if they are doing commit_at, ensure the input is formatted correctly.
    if value is not None:
        if (re.search(r'([0-2]\d)(:[0-5]\d){1,2}', value) is None and
            re.search(r'\d{4}-[01]\d-[0-3]\d [0-2]\d:[0-5]\d(:[0-5]\d)?',
                      value) is None):
            raise click.BadParameter("A commit at time must be in one of the "
                                     "two formats: 'hh:mm[:ss]' or "
                                     "'yyyy-mm-dd hh:mm[:ss]' (seconds are "
                                     "optional).")
    ctx.obj['at_time'] = value


@main.command(context_settings=CONTEXT_SETTINGS)
@click.argument('commands', required=True)
@click.option('--check/--no-check', default=False, help="Flag to indicate to"
              "only do a commit check. Defaults to False.")
#TODO: compare only
@click.option('--sync/--no-sync', default=False, help="Flag to indicate to"
              "make the commit synchronize between routing engines. Defaults"
              " to false.")
@click.option('-c', '--comment', help="Accepts a string to be commented in the"
              " system commit log.")
@click.option('-C', '--confirm', type=click.IntRange(60, 7200), help="Specify"
              " a commit confirmed timeout, **in seconds**. If the device "
              " does not receive another commit within the timeout, the "
              "changes will be rolled back. Allowed range is 60 to 7200 "
              "seconds.")
@click.option('-a', '--at', 'at_time', callback=at_time_validate,
              help="Specify the time at which the commit should occur. "
              "Can be in one of two formats: hh:mm[:ss]  or  yyyy-mm-dd "
              "hh:mm[:ss]")
@click.pass_context
def commit(ctx, commands, check, sync, comment, confirm, at_time):
    """Execute a commit against the device.

    Purpose: This function will send set commands to a device, and commit
           | the changes. Options exist for confirming, comments,
           | synchronizing, checking, or delaying.

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
    # add the 'show | compare' output.
    secho("show | compare:\n", 'info', file=ctx.obj['out'])
    click.echo(ctx.obj['jaide'].compare_config(commands),
               file=ctx.obj['out'])
    # If they just want to validate the config, without committing
    if check:
        secho("Commit check results from: %s" % ctx.obj['jaide'].host, 'info',
              file=ctx.obj['out'])
        try:
            click.echo(ctx.obj['jaide'].commit_check(commands),
                       file=ctx.obj['out'])
        except RPCError:
            secho("Uncommitted changes left on the device or someone else is"
                  " in edit mode, couldn't lock the candidate configuration.",
                  'error', file=ctx.obj['out'])
        except:
            secho("Failed to commit check on device %s for an unknown reason."
                  % ctx.obj['jaide'].host, 'error', file=ctx.obj['out'])
    # Actually make a commit
    else:
        secho("Attempting to commit on device: %s" % ctx.obj['jaide'].host,
              'info', file=ctx.obj['out'])
        try:
            results = ctx.obj['jaide'].commit(confirmed=confirm,
                                              comment=comment,
                                              at_time=ctx.obj['at_time'],
                                              synchronize=sync,
                                              commands=commands)
        except RPCError as e:
            secho('Commit could not be completed on this device, due to the '
                  'following error: \n' + str(e), 'error', file=ctx.obj['out'])
        else:
            if 'commit complete' in results:
                click.echo(results.split('commit complete')[0],
                           file=ctx.obj['out'])
                secho('Commit complete on device: ' + ctx.obj['jaide'].host,
                      file=ctx.obj['out'])
                if confirm:
                    secho('Commit confirm will rollback in %s minutes unless '
                          'you commit again' % str(confirm / 60),
                          file=ctx.obj['out'])
            elif 'commit at' in results:
                click.echo(results.split('commit at will be executed at')[0],
                           file=ctx.obj['out'])
                secho('Commit staged to happen at: %s' % ctx.obj['at_time'],
                      file=ctx.obj['out'])
            else:
                if 'failed' in results:
                    click.echo(results.replace('failed', color('failed',
                               'error')), file=ctx.obj['out'])
                if 'error' in results:
                    click.echo(results.replace('error', color('error',
                               'error')), file=ctx.obj['out'])
                secho('Commit Failed on device: ' + ctx.obj['jaide'].host,
                      'error', file=ctx.obj['out'])


@main.command(context_settings=CONTEXT_SETTINGS)
@click.argument('source', type=click.Path())
@click.argument('destination', type=click.Path(resolve_path=True))
@click.option('--progress/--no-progress', default=False, help="Flag to show "
              "progress as the transfer happens. Defaults to False")
# TODO: will need to set ctx.obj['multi'] tracking multi devices to know if we're renaming the output file.
@click.pass_context
def scp_pull(ctx, source, destination, progress):
    """ SCP copy file(s) from the device.

    @param conn: The Jaide session object for the device
    @type conn: jaide.Jaide object
    @param direction: the direction of the copy, either 'push' or 'pull'
    @type direction: str
    @param source: the source filepath or dirpath
    @type source: str
    @param destination: the destination filepath or dirpath
    @type destination: str
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
    secho('Retrieving %s:%s, and putting it in %s' %
          (ctx.obj['jaide'].host, source, path.normpath(destination)), 'info')
    # Check if the destination ends in a '/', if not, we need to add it.
    destination = destination + '/' if destination[-1] != '/' else destination
    # If the source ends in a slash, we need to remove it. For copying
    # directories, this will ensure that the local directory gets created
    # remotely, and not just the contents. Basically, this forces the behavior
    # 'scp -r /var/log /dest/loc' instead of 'scp -r /var/log/* /dest/loc'
    source = source[:-1] if source[-1] == '/' else source
    try:
        ctx.obj['jaide'].scp_pull(source, destination, progress)
        if progress:
            click.echo('', file=ctx.obj['out'])
    except SCPException as e:
        secho('!!! Error during copy from ' + ctx.obj['jaide'].host +
              '. Some files may have failed to transfer. SCP Module error:\n'
              + str(e) + ' !!!\n', 'error', file=ctx.obj['out'])
    except (IOError, OSError) as e:
        secho('!!! The local filepath was not found! Note that \'~\' cannot be'
              ' used. Error:\n' + str(e) + ' !!!\n',
              'error', file=ctx.obj['out'])
    else:
        secho('Received %s:%s and stored it in %s.\n' %
              (ctx.obj['jaide'].host, source, path.normpath(destination)))


@main.command(context_settings=CONTEXT_SETTINGS)
@click.argument('source', type=click.Path(exists=True, resolve_path=True))
@click.argument('destination', type=click.Path())
@click.option('--progress/--no-progress', default=False, help="Flag to show "
              "progress as the transfer happens. Defaults to False")
# TODO: will need to set ctx.obj['multi'] tracking multi devices to know if we're renaming the output file.
@click.pass_context
def scp_push(ctx, source, destination, progress):
    """ SCP copy file(s) to the device.

    @param conn: The Jaide session object for the device
    @type conn: jaide.Jaide object
    @param direction: the direction of the copy, either 'push' or 'pull'
    @type direction: str
    @param source: the source filepath or dirpath
    @type source: str
    @param destination: the destination filepath or dirpath
    @type destination: str
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
    secho('Pushing %s to %s:%s' % (source, ctx.obj['jaide'].host,
                                   destination), 'info', file=ctx.obj['out'])
    # Check if the destination ends in a '/', if not, we need to add it.
    destination = destination + '/' if destination[-1] != '/' else destination
    # If the source ends in a slash, we need to remove it. For copying
    # directories, this will ensure that the local directory gets created
    # remotely, and not just the contents. Basically, this forces the behavior
    # 'scp -r /var/log /dest/loc' instead of 'scp -r /var/log/* /dest/loc'
    source = source[:-1] if source[-1] == '/' else source
    try:
        ctx.obj['jaide'].scp_push(source, destination, progress)
        if progress:
            click.echo('', file=ctx.obj['out'])
    except SCPException as e:
        secho('!!! Error during copy from ' + ctx.obj['jaide'].host +
              '. Some files may have failed to transfer. SCP Module error:\n'
              + str(e) + ' !!!\n', 'error', file=ctx.obj['out'])
    except (IOError, OSError) as e:
        secho('!!! The local filepath was not found! Note that \'~\' cannot '
              'be used. Error:\n' + str(e) + ' !!!\n', 'error',
              file=ctx.obj['out'])
    else:
        secho('Pushed %s to %s:%s' % (source, ctx.obj['jaide'].host,
                                      destination), file=ctx.obj['out'])


@main.command(context_settings=CONTEXT_SETTINGS)
@click.argument('commands', required=True)
@click.option('-f', '--format', type=click.Choice(['text', 'xml']),
              default='text', help="The requested format of the response.")
@click.option('-x', '--xpath', required=False, help="An xpath expression"
              " that will filter the results. Forces response format xml."
              " Example: '//rt-entry'")
@click.pass_context
def command(ctx, commands, format, xpath):
    """ Execute operational mode command(s).

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
    for cmd in clean_lines(commands):
        secho('> ' + cmd, 'info', file=ctx.obj['out'])
        # Get xpath expression from the command, if it is there.
        # If there is an xpath expr, the output will be xml,
        # overriding the req_format parameter
        #
        # Example command forcing xpath: show route % //rt-entry
        if len(cmd.split('%')) == 2:
            xpath = cmd.split('%')[1].strip()
            cmd = cmd.split('%')[0] + '\n'
        if xpath:
            try:
                click.echo(ctx.obj['jaide'].op_cmd(command=cmd,
                           req_format='xml', xpath_expr=xpath),
                           file=ctx.obj['out'])
            except lxml.etree.XMLSyntaxError:
                secho('Xpath expression resulted in no response.', 'error')
        else:
            click.echo(ctx.obj['jaide'].op_cmd(cmd, req_format=format),
                       file=ctx.obj['out'])


@main.command(name='info', context_settings=CONTEXT_SETTINGS)
@click.pass_context
def device_info(ctx):
    """Get basic device information."""
    click.echo(ctx.obj['jaide'].device_info(), file=ctx.obj['out'])


@main.command(context_settings=CONTEXT_SETTINGS)
@click.option('-o', '--second-host', required=True, help="The second"
              " hostname or IP address to compare against.")
@click.option('-m', '--mode', type=click.Choice(['set', 'stanza']),
              default='set', help="How to view the differences. Can be"
              " either 'set' or 'stanza'. Defaults to 'set'")
@click.pass_context
def diff_config(ctx, second_host, mode):
    """ Config comparison between two devices.

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
                            ctx.obj['jaide'].diff_config(second_host,
                                                         mode.lower())])
    except errors.AuthenticationError:  # NCClient auth failure
        secho('Authentication failed for device: %s\n' %
              second_host, 'error', file=ctx.obj['out'])
    except AuthenticationException:  # Paramiko auth failure
        secho('Authentication failed for device: %s\n' %
              second_host, 'error', file=ctx.obj['out'])
    except SSHException as e:
        secho('Error connecting to device: %s\nError: %s' %
              (second_host, str(e)), 'error', file=ctx.obj['out'])
    except socket.timeout:
        secho('Timeout exceeded connecting to device: %s\n' %
              second_host, 'error', file=ctx.obj['out'])
    if output.strip() == '':
        secho("There were no config differences between %s and %s\n" %
              (ctx.obj['jaide'].host, second_host), file=ctx.obj['out'])
    else:
        # color removals as errors, and additions as success
        output = output.replace('---', color('---', 'error'))
        output = output.replace('+++', color('+++'))
        output = output.replace('\n-', color('\n-', 'error'))
        output = output.replace('\n+', color('\n+'))
        output = output.replace('@@', color('@@', 'info'))
    click.echo(output, file=ctx.obj['out'])


@main.command(name="health", context_settings=CONTEXT_SETTINGS)
@click.pass_context
def health_check(ctx):
    """ Get alarm and device health information. """
    click.echo(ctx.obj['jaide'].health_check(), file=ctx.obj['out'])


@main.command(name="errors", context_settings=CONTEXT_SETTINGS)
@click.pass_context
def interface_errors(ctx):
    """Get any interface errors from the device."""
    response = ctx.obj['jaide'].interface_errors()
    if 'No interface errors' in response:
        secho(response, file=ctx.obj['out'])
    else:
        secho(response, 'error', file=ctx.obj['out'])


@main.command(context_settings=CONTEXT_SETTINGS)
@click.argument('commands', required=True)
@click.pass_context
def shell(ctx, commands):
    """ Send bash command(s) to the device(s). """
    for cmd in clean_lines(commands):
        secho('> ' + cmd, 'info', file=ctx.obj['out'])
        click.echo(ctx.obj['jaide'].shell_cmd(cmd), file=ctx.obj['out'])


if __name__ == '__main__':
    main(obj={})
