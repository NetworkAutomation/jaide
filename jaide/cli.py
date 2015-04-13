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
from __future__ import print_function
# standard modules
import os
from os import path, popen
import multiprocessing
import re
# intra-Jaide imports
import wrap
from utils import clean_lines
from color_utils import color
# non-standard modules:
import click

# TODO: new option to suppress color highlighting?

# needed for '-h' to be a help option
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class AliasedGroup(click.Group):

    """ Extends click.Group to allow for partial commands. """

    def get_command(self, ctx, cmd_name):
        """ Allow for partial commands. """
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx)
                   if x.startswith(cmd_name)]
        if not matches:
            return None
        elif len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])
        ctx.fail('Command ambiguous, could be: %s' %
                 ', '.join(sorted(matches)))


def at_time_validate(ctx, param, value):
    """ Callback validating the at_time commit option.

    Purpose: Validates the `at time` option for the commit command. Only the
           | the following two formats are supported: 'hh:mm[:ss]' or
           | 'yyyy-mm-dd hh:mm[:ss]' (seconds are optional).

    @param ctx: The click context paramter, for receiving the object dictionary
              | being manipulated by other previous functions. Needed by any
              | function with the @click.pass_context decorator. Callback
              | functions such as this one receive this automatically.
    @type ctx: click.Context
    @param param: param is passed into a validation callback function by click.
                | We do not use it.
    @type param: None
    @param value: The value that the user supplied for the at_time option.
    @type value: str

    @returns: The value that the user supplied, if it passed validation.
            | Otherwise, raises click.BadParameter
    @rtype: str
    """
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
    return value


@click.pass_context
def write_validate(ctx, param, value):
    """ Validate the -w option.

    Purpose: Validates the `-w`|`--write` option. Two arguments are expected.
           | The first is the mode, which must be in ['s', 'single', 'm',
           |  'multiple']. The mode determins if we're writing to one file for
           | all device output, or to a separate file for each device being
           | handled.
           |
           | The second expected argument is the filepath of the desired
           | output file. This will automatically be prepended with the IP or
           | hostname of the device if we're writing to multiple files.

    @param ctx: The click context paramter, for receiving the object dictionary
              | being manipulated by other previous functions. Needed by any
              | function with the @click.pass_context decorator. Callback
              | functions such as this one receive this automatically.
    @type ctx: click.Context
    @param param: param is passed into a validation callback function by click.
                | We do not use it.
    @type param: None
    @param value: The value that the user supplied for the write option.
    @type value: str

    @returns: The value that the user supplied, if it passed validation.
            | Otherwise, raises click.BadParameter
    @rtype: str
    """
    if value != ("default", "default"):
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
        # we've passed the checks, so set the 'out' context variable to our
        # tuple of the mode, and the destination file.
        ctx.obj['out'] = (mode.lower(), dest_file)
    else:  # they didn't use -w, so set the context variable accordingly.
        ctx.obj['out'] = None


def write_out(input):
    """ Callback function to write the output from the script.

    @param input: A tuple containing two things:
                | 1. None or Tuple of file mode and destination filepath
                | 2. The output of the jaide command that will be either
                |    written to sys.stdout or to a file, depending on the
                |    first index in the tuple.
                |
                | If the first index of the tuple *is not* another tuple,
                | the output will be written to sys.stdout. If the first
                | index *is* a tuple, that tuple is further broken down
                | into the mode ('single' for single file or 'multiple'
                | for one file for each IP), and the destination filepath.
    @type input: tuple

    @returns: None
    """
    # peel off the to_file metadata from the output.
    to_file, output = input
    if to_file != "quiet":
        try:
            # split the to_file metadata into it's separate parts.
            mode, dest_file = to_file
        except TypeError:
            # just dump the output if we had an internal problem with getting
            # the metadata.
            click.echo(output)
        else:
            ip = output.split('device: ')[1].split('\n')[0].strip()
            if mode in ['m', 'multiple']:
                # put the IP in front of the filename if we're writing each
                # device to its own file.
                dest_file = path.join(path.split(dest_file)[0], ip + "_" +
                                      path.split(dest_file)[1])
            try:
                out_file = open(dest_file, 'a+b')
            except IOError as e:
                print(color("Could not open output file '%s' for writing. "
                            "Output would have been:\n%s" %
                            (dest_file, output), 'red'))
                print(color('Here is the error for opening the output file:' +
                            str(e), 'red'))
            else:
                click.echo(output, nl=False, file=out_file)
                print(color('%s output appended to: %s' % (ip, dest_file)))
                out_file.close()


@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS,
             help="Manipulate one or more Junos devices.\n\nWill connect to "
             "one or more Junos devices, and manipulate them based on the "
             "command you have chosen. If a comma separated list or a file "
             "containing IP/hostnames on each line is given for the IP option,"
             " the commands will be sent simultaneously to each device.")
@click.option('-i', '--ip', 'host', prompt="IP or hostname of Junos device",
              help="The target hostname(s) or IP(s). Can be a comma separated"
              " list, or path to a file listing devices on individual lines.")
@click.option('-u', '--username', prompt="Username")
@click.password_option('-p', '--password', prompt="Password")
@click.option('-P', '--port', default=22, help="The port to connect to. "
              "Defaults to SSH (22)")
@click.option('--quiet/--no-quiet', default=False, help="Boolean flag to show"
              " no output, except in certain error scenarios. Defaults to "
              "false (--no-quiet), which shows the output.")
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
              callback=write_validate, help="Write the output to a file "
              "instead of echoing it to the terminal. This can be useful "
              "when touching more than one device, because the output can be "
              "split into a file per device. In this case, output filename "
              "format is IP_FILENAME.", metavar="[s | single | m | multiple]"
              " FILEPATH", default=("default", "default"))
@click.pass_context
def main(ctx, host, password, port, quiet, session_timeout, connect_timeout,
         username):
    """ Manipulate one or more Junos devices.

    Purpose: The main function is the entry point for the jaide tool. Click
           | handles arguments, commands and options. The parameters passed to
           | this function are all potential options (required or not) that
           | must come *before* the command from the group in the command line.

    @param ctx: The click context paramter, for receiving the object dictionary
              | being manipulated by other previous functions. Needed by any
              | function with the @click.pass_context decorator.
    @type ctx: click.Context
    @param host: The IP(s) or hostname(s) of the devices to connect to.
    @type host: str
    @param password: The string password used to connect to the device.
    @type password: str
    @param port: The numerical port to establish the connection to. Defauls
               | to 22.
    @type port: int
    @param quiet: An option that the user can set to suppress all output
                | from jaide.
    @type quiet: bool
    @param session_timeout: Sets the session timeout value. A higher value may
                          | be desired for long running commands, such as
                          | 'request system snapshot slice alternate'
    @type session_timeout: int
    @param connect_timeout: Sets the connection timeout value. This is how
                          | we'll wait when connecting before classifying
                          | the device unreachable.
    @type connect_timeout: int
    @param username: The string username used to connect to the device.
    @type useranme: str

    @returns: None. Functions part of click relating to the command group
            | 'main' do not return anything. Click handles passing context
            | between the functions and maintaing command order and chaining.
    """
    # build the list of hosts
    ctx.obj['hosts'] = [ip for ip in clean_lines(host)]
    # set the connection parameters
    ctx.obj['conn'] = {
        "username": username,
        "password": password,
        "port": port,
        "session_timeout": session_timeout,
        "connect_timeout": connect_timeout
    }
    if quiet:
        ctx.obj['out'] = "quiet"


@main.command(context_settings=CONTEXT_SETTINGS, help="Execute a commit "
              "against the device.\n\nThis command will send set commands to"
              " a device, and commit the changes. Options exist for "
              "confirming, comments, synchronizing, checking, blank commits,"
              " or delaying to a later time/date.")
@click.argument('commands', default='annotate system ""', required=True)
@click.option('--blank/--no-blank', default=False, help="Flag to indicate to"
              " make a commit with no changes. Defaults to False. Functionally"
              " this commits one set command: 'annotate system'")
@click.option('--check/--no-check', default=False, help="Flag to indicate to"
              " only do a commit check. Defaults to False.")
@click.option('--sync/--no-sync', default=False, help="Flag to indicate to"
              "make the commit synchronize between routing engines. Defaults"
              " to false.")
@click.option('-c', '--comment', help="Accepts a string to be commented in the"
              " system commit log.")
@click.option('-C', '--confirm', type=click.IntRange(60, 7200), help="Specify"
              " a commit confirmed timeout, **in seconds**. If the device "
              " does not receive another commit within the timeout, the "
              "changes will be rolled back. Allowed range is 60 to 7200 "
              "seconds. --confirm and --at are mutually exclusive, and confirm"
              " will override.")
@click.option('-a', '--at', 'at_time', callback=at_time_validate,
              help="Specify the time at which the commit should occur. "
              "--at and --confirm are mutually exclusive, and confirm will"
              " override. Can be in one of two formats: hh:mm[:ss]  or  "
              "yyyy-mm-dd hh:mm[:ss]")
@click.pass_context
def commit(ctx, commands, blank, check, sync, comment, confirm, at_time):
    """ Execute a commit against the device.

    Purpose: This function will send set commands to a device, and commit
           | the changes. Options exist for confirming, comments,
           | synchronizing, checking, blank commits, or delaying to a later
           | time/date.

    @param ctx: The click context paramter, for receiving the object dictionary
              | being manipulated by other previous functions. Needed by any
              | function with the @click.pass_context decorator.
    @type ctx: click.Context
    @param commands: String containing the set command to be sent to the
                   | device. It can be a python list of strings, a single set
                   | command, a comma separated string of commands, or a
                   | string filepath pointing to a file with set commands
                   | on each line.
    @type commands: str or list
    @param blank: A bool set to true to only make a blank commit. A blank
                | commit makes a commit, but doesn't have any set commands
                | associated with it, so no changes are made, but a commit
                | does happen.
    @type blank: bool
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

    @returns: None. Functions part of click relating to the command group
            | 'main' do not return anything. Click handles passing context
            | between the functions and maintaing command order and chaining.
    """
    if not blank and commands == 'annotate system ""':
        raise click.BadParameter("--blank and the commands argument cannot"
                                 " both be omitted.")
    mp_pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
    for ip in ctx.obj['hosts']:
        mp_pool.apply_async(wrap.open_connection, args=(ip,
                            ctx.obj['conn']['username'],
                            ctx.obj['conn']['password'],
                            wrap.commit,
                            [commands, check, sync, comment, confirm,
                             ctx.obj['at_time'], blank],
                            ctx.obj['out'],
                            ctx.obj['conn']['connect_timeout'],
                            ctx.obj['conn']['session_timeout'],
                            ctx.obj['conn']['port']), callback=write_out)
    mp_pool.close()
    mp_pool.join()


@main.command(context_settings=CONTEXT_SETTINGS, help="Compare commands"
              " against running config.\n"
              "\n COMMANDS can be a single set command, a comma separated list"
              " of commands, or a filepath pointing to a file of set commands "
              "on each line.")
@click.argument('commands', required=True)
@click.pass_context
def compare(ctx, commands):
    """ Run 'show | compare' for set commands.

    @param ctx: The click context paramter, for receiving the object dictionary
              | being manipulated by other previous functions. Needed by any
              | function with the @click.pass_context decorator.
    @type ctx: click.Context
    @param commands: The Junos set commands that will be put into a candidate
                   | configuration and used to create the 'show | compare'
                   | against the running configuration. much like the commands
                   | parameter for the commit() function, this can be one of
                   | three things: a string containing a single command, a
                   | string containing a comma separated list of commands, or
                   | a string containing a filepath location for a file with
                   | commands on each line.
    @type commands: str

    @returns: None. Functions part of click relating to the command group
            | 'main' do not return anything. Click handles passing context
            | between the functions and maintaing command order and chaining.
    """
    mp_pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
    for ip in ctx.obj['hosts']:
        mp_pool.apply_async(wrap.open_connection, args=(ip,
                            ctx.obj['conn']['username'],
                            ctx.obj['conn']['password'],
                            wrap.compare, [commands],
                            ctx.obj['out'],
                            ctx.obj['conn']['connect_timeout'],
                            ctx.obj['conn']['session_timeout'],
                            ctx.obj['conn']['port']), callback=write_out)
    mp_pool.close()
    mp_pool.join()


@main.command(context_settings=CONTEXT_SETTINGS, help="Copy file(s) from "
              "device(s) -> local machine.\n\nThe source can be a single file"
              ", or a directory containing many files. If you run into "
              "permissions errors, try using the root account.")
@click.argument('source', type=click.Path())
@click.argument('destination', type=click.Path(resolve_path=True))
@click.option('--progress/--no-progress', default=False, help="Flag to show "
              "progress as the transfer happens. Defaults to False for "
              "multiple devices, as output will be jumbled.")
@click.pass_context
def pull(ctx, source, destination, progress):
    """ Copy file(s) from device(s) -> local machine.

    @param ctx: The click context paramter, for receiving the object dictionary
              | being manipulated by other previous functions. Needed by any
              | function with the @click.pass_context decorator.
    @type ctx: click.Context
    @param source: the source filepath or dirpath
    @type source: str
    @param destination: the destination filepath or dirpath
    @type destination: str
    @param progress: bool set to True if we should request a progress callback
                   | from the Jaide object. Always set to False when
                   | we're copying to/from multiple devices.
    @type progress: bool

    @returns: None. Functions part of click relating to the command group
            | 'main' do not return anything. Click handles passing context
            | between the functions and maintaing command order and chaining.
    """
    mp_pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
    multi = True if len(ctx.obj['hosts']) > 1 else False
    for ip in ctx.obj['hosts']:
        mp_pool.apply_async(wrap.open_connection, args=(ip,
                            ctx.obj['conn']['username'],
                            ctx.obj['conn']['password'],
                            wrap.pull, [source, destination, progress, multi],
                            ctx.obj['out'],
                            ctx.obj['conn']['connect_timeout'],
                            ctx.obj['conn']['session_timeout'],
                            ctx.obj['conn']['port']), callback=write_out)
    mp_pool.close()
    mp_pool.join()


@main.command(context_settings=CONTEXT_SETTINGS, help="Copy file(s) from "
              "local machine -> device(s).\n\nThe source can be a single file"
              ", or a directory containing many files. If you run into "
              "permissions errors, try using the root account.")
@click.argument('source', type=click.Path(exists=True, resolve_path=True))
@click.argument('destination', type=click.Path())
@click.option('--progress/--no-progress', default=False, help="Flag to show "
              "progress as the transfer happens. Defaults to False for "
              "multiple devices, as output would be jumbled.")
@click.pass_context
def push(ctx, source, destination, progress):
    """ Copy file(s) from local machine -> device(s).

    @param ctx: The click context paramter, for receiving the object dictionary
              | being manipulated by other previous functions. Needed by any
              | function with the @click.pass_context decorator.
    @type ctx: click.Context
    @param source: the source filepath or dirpath
    @type source: str
    @param destination: the destination filepath or dirpath
    @type destination: str
    @param progress: bool set to True if we should request a progress callback
                   | from the Jaide object. Always set to False when
                   | we're copying to/from multiple devices.
    @type progress: bool

    @returns: None. Functions part of click relating to the command group
            | 'main' do not return anything. Click handles passing context
            | between the functions and maintaing command order and chaining.
    """
    mp_pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
    for ip in ctx.obj['hosts']:
        mp_pool.apply_async(wrap.open_connection, args=(ip,
                            ctx.obj['conn']['username'],
                            ctx.obj['conn']['password'],
                            wrap.push, [source, destination, progress],
                            ctx.obj['out'],
                            ctx.obj['conn']['connect_timeout'],
                            ctx.obj['conn']['session_timeout'],
                            ctx.obj['conn']['port']), callback=write_out)
    mp_pool.close()
    mp_pool.join()


@main.command(context_settings=CONTEXT_SETTINGS, help="Execute operational "
              "mode command(s).\n\nMore than one command can be sent as a "
              "comma separated list, or as a filepath containing a command on"
              " each line.")
@click.argument('commands', required=True)
@click.option('-f', '--format', type=click.Choice(['text', 'xml']),
              default='text', help="The requested format of the response.")
@click.option('-x', '--xpath', required=False, help="An xpath expression"
              " that will filter the results. Forces response format xml."
              " Example: '//rt-entry'")
@click.pass_context
def operational(ctx, commands, format, xpath):
    """ Execute operational mode command(s).

    This function will send operational mode commands to a Junos
    device. jaide.utils.clean_lines() is used to determine how we are
    receiving commands, and ignore comment lines or blank lines in
    a command file.

    @param ctx: The click context paramter, for receiving the object dictionary
              | being manipulated by other previous functions. Needed by any
              | function with the @click.pass_context decorator.
    @type ctx: click.Context
    @param commands: The op commands to send to the device. Can be one of
                   | four things:
                   |    1. A single op command as a string.
                   |    2. A string of comma separated op commands.
                   |    3. A python list of op commands.
                   |    4. A filepath of a file with op commands on each
                   |         line.
    @type commands: str
    @param format: String specifying what format to request for the
                 | response from the device. Defaults to 'text', but
                 | also accepts 'xml'.
    @type format: str
    @param xpath: An xpath expression on which we should filter the results.
                | This enforces 'xml' for the format of the response.
    @type xpath: str

    @returns: None. Functions part of click relating to the command group
            | 'main' do not return anything. Click handles passing context
            | between the functions and maintaing command order and chaining.
    """
    mp_pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
    for ip in ctx.obj['hosts']:
        mp_pool.apply_async(wrap.open_connection, args=(ip,
                            ctx.obj['conn']['username'],
                            ctx.obj['conn']['password'],
                            wrap.command, [commands, format, xpath],
                            ctx.obj['out'],
                            ctx.obj['conn']['connect_timeout'],
                            ctx.obj['conn']['session_timeout'],
                            ctx.obj['conn']['port']), callback=write_out)
    mp_pool.close()
    mp_pool.join()


@main.command(name='info', context_settings=CONTEXT_SETTINGS, help="Get basic"
              " device information.")
@click.pass_context
def device_info(ctx):
    """ Get basic device information.

    @param ctx: The click context paramter, for receiving the object dictionary
              | being manipulated by other previous functions. Needed by any
              | function with the @click.pass_context decorator.
    @type ctx: click.Context
    """
    mp_pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
    for ip in ctx.obj['hosts']:
        mp_pool.apply_async(wrap.open_connection, args=(ip,
                            ctx.obj['conn']['username'],
                            ctx.obj['conn']['password'],
                            wrap.device_info, [],
                            ctx.obj['out'],
                            ctx.obj['conn']['connect_timeout'],
                            ctx.obj['conn']['session_timeout'],
                            ctx.obj['conn']['port']), callback=write_out)
    mp_pool.close()
    mp_pool.join()


@main.command(context_settings=CONTEXT_SETTINGS, help="Compare the "
              "config between two devices.\n\nFor help on "
              "reading the output, view the following page: "
              "http://www.git-tower.com/learn/ebook/command-line/advanced-"
              "topics/diffs")
@click.option('-i', '--second-host', required=True, help="The second"
              " hostname or IP address to compare against.")
@click.option('-m', '--mode', type=click.Choice(['set', 'stanza']),
              default='set', help="How to view the differences. Can be"
              " either 'set' or 'stanza'. Defaults to 'set'")
@click.pass_context
def diff_config(ctx, second_host, mode):
    """ Config comparison between two devices.

    @param ctx: The click context paramter, for receiving the object dictionary
              | being manipulated by other previous functions. Needed by any
              | function with the @click.pass_context decorator.
    @type ctx: click.Context
    @param second_host: The IP/hostname of the second device to pull from
    @type second_host: str
    @param mode: The mode in which we are retrieving the config ('set' or
               | 'stanza')
    @type mode: str

    @returns: None. Functions part of click relating to the command group
            | 'main' do not return anything. Click handles passing context
            | between the functions and maintaing command order and chaining.
    """
    mp_pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
    for ip in ctx.obj['hosts']:
        mp_pool.apply_async(wrap.open_connection, args=(ip,
                            ctx.obj['conn']['username'],
                            ctx.obj['conn']['password'],
                            wrap.diff_config, [second_host, mode],
                            ctx.obj['out'],
                            ctx.obj['conn']['connect_timeout'],
                            ctx.obj['conn']['session_timeout'],
                            ctx.obj['conn']['port']), callback=write_out)
    mp_pool.close()
    mp_pool.join()


@main.command(name="health", context_settings=CONTEXT_SETTINGS, help="Get "
              "alarm and device health information.")
@click.pass_context
def health_check(ctx):
    """ Get alarm and device health information.

    @param ctx: The click context paramter, for receiving the object dictionary
              | being manipulated by other previous functions. Needed by any
              | function with the @click.pass_context decorator.
    @type ctx: click.Context

    @returns: None. Functions part of click relating to the command group
            | 'main' do not return anything. Click handles passing context
            | between the functions and maintaing command order and chaining.
    """
    mp_pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
    for ip in ctx.obj['hosts']:
        mp_pool.apply_async(wrap.open_connection, args=(ip,
                            ctx.obj['conn']['username'],
                            ctx.obj['conn']['password'],
                            wrap.health_check, [],
                            ctx.obj['out'],
                            ctx.obj['conn']['connect_timeout'],
                            ctx.obj['conn']['session_timeout'],
                            ctx.obj['conn']['port']), callback=write_out)
    mp_pool.close()
    mp_pool.join()


@main.command(name="errors", context_settings=CONTEXT_SETTINGS, help="Get any"
              " interface errors from the device.")
@click.pass_context
def interface_errors(ctx):
    """ Get any interface errors from the device.

    @param ctx: The click context paramter, for receiving the object dictionary
              | being manipulated by other previous functions. Needed by any
              | function with the @click.pass_context decorator.
    @type ctx: click.Context

    @returns: None. Functions part of click relating to the command group
            | 'main' do not return anything. Click handles passing context
            | between the functions and maintaing command order and chaining.
    """
    mp_pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
    for ip in ctx.obj['hosts']:
        mp_pool.apply_async(wrap.open_connection, args=(ip,
                            ctx.obj['conn']['username'],
                            ctx.obj['conn']['password'],
                            wrap.interface_errors, [],
                            ctx.obj['out'],
                            ctx.obj['conn']['connect_timeout'],
                            ctx.obj['conn']['session_timeout'],
                            ctx.obj['conn']['port']), callback=write_out)
    mp_pool.close()
    mp_pool.join()


@main.command(context_settings=CONTEXT_SETTINGS, help="Send shell commands to "
              "the device(s).\n\nMultiple shell commands can be sent using a "
              "comma separate list, or a filepath to a file containing shell "
              "commands on each line.")
@click.argument('commands', required=True)
@click.pass_context
def shell(ctx, commands):
    """ Send bash command(s) to the device(s).

    @param ctx: The click context paramter, for receiving the object dictionary
              | being manipulated by other previous functions. Needed by any
              | function with the @click.pass_context decorator.
    @type ctx: click.Context
    @param commands: The shell commands to send to the device. Can be one of
                   | four things:
                   |    1. A single shell command as a string.
                   |    2. A string of comma separated shell commands.
                   |    3. A python list of shell commands.
                   |    4. A filepath of a file with shell commands on each
                   |         line.
    @type commands: str or list

    @returns: None. Functions part of click relating to the command group
            | 'main' do not return anything. Click handles passing context
            | between the functions and maintaing command order and chaining.
    """
    mp_pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
    for ip in ctx.obj['hosts']:
        mp_pool.apply_async(wrap.open_connection, args=(ip,
                            ctx.obj['conn']['username'],
                            ctx.obj['conn']['password'],
                            wrap.shell, [commands],
                            ctx.obj['out'],
                            ctx.obj['conn']['connect_timeout'],
                            ctx.obj['conn']['session_timeout'],
                            ctx.obj['conn']['port']), callback=write_out)
    mp_pool.close()
    mp_pool.join()


def run():
    if os.name == 'posix':
        # set max_content_width to the width of the terminal dynamically
        rows, columns = popen('stty size', 'r').read().split()
        # obj and max_column_width get passed into click, and don't actually
        # proceed into the main() command group. Click handles the CLI
        # user options and passing them into main().
        main(obj={}, max_content_width=int(columns))
    else:
        main(obj={})

if __name__ == '__main__':
    run()
