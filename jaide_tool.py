"""Jaide CLI script for manipulating Junos devices.

This is the cli script that is a base use case of the jaide module.
It creates a command line tool for using the jaide module, to allow for
communicating with, manipulating, and many other functions with Junos based
devices.

For expansive information on the Jaide script, and how JGUI interacts with it,
refer to the readme file or the associated examples/documentation.

We have provided some information about NCClient here, since it can get
confusing in some situations.

    manager.command() can be run with format = 'xml' or 'text', and returns an
    XML object or string

    manager.command() returns an NCElement object with a .tostring attribute
    and an xpath() function

    Using .tostring will return a text string of the values of all leaves
    within the xml tree.

    Using xpath() will return an array of xml leaves, that each has the text
    property for returning the value of a leaf.

    By default, a show config command run on JUNOS does not return with full
    XML tags and cannot be explicitly xpath'd. To do xpath on a show config
    command, explicitly include '| display xml' on the end of the command
    before handing off to manager.command().

    On Junos, non-config commands can be run with '| display xml rpc' appended
    to get the rpc command.
"""
from os import path
import multiprocessing
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import getpass
import re
from jaide import Jaide, clean_lines
from ncclient.transport import errors
from paramiko import SSHException, AuthenticationException
import socket

# -i is a required parameter, the rest are optional arguments
prs = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                     description="Required Modules:\n\tNCCLIENT - "
                     "https://github.com/leopoul/ncclient/ \n\tPARAMIKO - "
                     "https://github.com/paramiko/paramiko \n\tSCP - "
                     "https://pypi.python.org/pypi/scp/\n\nThis script can be "
                     "used as an aide to easily do the same command(s) to "
                     "multiple juniper devices. The only required arguments "
                     "are the destination IP address(es) or host(s), and one "
                     "of the following commands:\nSingle Format: "
                     "\t[ -c | -e | -H | -I | -s | -S | -l | -b ]\nName Format"
                     ": \t[ --command | --errors | --health | --info | --set |"
                     " --scp | --shell | --blank ]", prog='jaide_tool.py',
                     usage="%(prog)s -i IP [-c operational_mode_commands | -e "
                     "| -H | -I | -s set_commands | -S [push | pull] source "
                     "destination | -l shell_commands | -b]")
prs.add_argument("-i", "--ip", required=True, dest='ip', type=str, help="The "
                 "target device(s) to run the script against. This can be a "
                 "single target device IP address/hostname, a quoted comma "
                 "separated list of IP's, or a filepath to a file containing "
                 "IP's on each line. Hostnames are resolved.")
prs.add_argument("-u", "--username", dest='username', type=str,
                 default='default', help="Will prompt if not specified.")
prs.add_argument("-p", "--password", dest='password', type=str,
                 default='default', help="Will prompt if not specified.")
prs.add_argument("-w", "--write", dest='write', metavar=("[s/single | "
                 "m/multiple]", "OUTPUT_FILENAME"), nargs=2, type=str,
                 help="Specify a filename to write all script output. Also "
                 "requires whether to write to a single file or a separate "
                 "file per IP. (ex. -w s ~/Desktop/output.txt). The output "
                 "format for the names of multiple files is IP_FILENAME.")
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
prs.add_argument("-P", "--port", dest="port", type=int, default=22,
                 help="Specify the port on which to connect to the device."
                 "Defaults to 22.")
prs.add_argument("-f", "--format", dest="format", type=str, default='text',
                 metavar='[ text | xml ]', help="Formats output to text or"
                 " xml. Should be used with -c. Default format is text. "
                 "Including an xpath expression after a command forces XML"
                 " output (EX. \"show route %% //rt-entry\").")

# Script functions: Must select one and only one.
group1 = prs.add_mutually_exclusive_group(required=True)
group1.add_argument("-c", "--command", dest='command', metavar="[operational_"
                    "mode_commands | file_of_operational_commands]", type=str,
                    help="Send a single operational mode command to device(s)."
                    " A trailing '%%' followed by an xpath expression will "
                    "filter the xml results by that expression. For example: "
                    "'show route %% //rt-entry'")
group1.add_argument("-e", "--errors", dest='int_error', action='store_true',
                    help='Check all interfaces for errors.')
group1.add_argument("-H", "--health", dest="health_check", action="store_true",
                    help="Grab a Health Check: CPU/Mem usage, alarms, etc from"
                    " the device.")
group1.add_argument("-I", "--info", dest='info', action='store_true',
                    help="Get basic device info (Serial #, Model, etc).")
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
group1.add_argument("-l", "--shell", dest='shell', metavar="[shell_commands | "
                    "file_of_shell_commands]", type=str, help="Similar to -c, "
                    "except it will run the commands from shell instead of "
                    "operational mode.")
group1.add_argument("-b", "--blank", dest="commit_blank", action='store_true',
                    help="Can be used with or without -s to make a blank "
                    "commit. A key use case is when trying to confirm a commit"
                    " confirm. --confirm, --check, --blank, and --at are "
                    "mutually exclusive!")

# Commit options. These options are mutually exclusive.
group2 = prs.add_mutually_exclusive_group()
group2.add_argument("-m", "--confirm", dest='commit_confirm',
                    metavar="CONFIRM_MINUTES", type=int, choices=range(1, 61),
                    help="Can be used with -s to make a confirmed commit. "
                    "Accepts a number in /minutes/ between 1 and 60! --confirm"
                    ", --check, --blank, and --at are mutually exclusive!")
group2.add_argument("-k", "--check", dest="commit_check", action='store_true',
                    help="Can be used with -s to only run a commit check, and"
                    " not commit the changes. --confirm, --check, --blank, and"
                    " --at are mutually exclusive!")
group2.add_argument("-a", "--at", dest='commit_at', type=str,
                    metavar="COMMIT_AT_TIME", help="Specify a time for the "
                    "device to make the commit at. Junos expects one of two "
                    "formats: A time value of the form 'hh:mm[:ss]' or a date "
                    "and time value of the form 'yyyy-mm-dd hh:mm[:ss]' "
                    "(seconds are optional).")

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
                    conn_timeout=5, sess_timeout=300, port=22):
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

    @returns: The string output that should displayed to the user, which
            | eventually makes it to the write_output() function.
    @rtype: str
    """
    # start with the header line on the output.
    output = '=' * 50 + '\nResults from device: %s\n' % ip
    print ip, username, password, function
    # this is used to track the filepath that we will output to. The
    # write_output() function will pick this up.
    if write_to_file:
        output += "*****WRITE_TO_FILE*****" + write_to_file[1] + \
                  "*****WRITE_TO_FILE*****" + write_to_file[0] + \
                  "*****WRITE_TO_FILE*****"
    try:
        # create the Jaide session object for the device.
        conn = Jaide(ip, username, password, conn_timeout=conn_timeout,
                     sess_timeout=sess_timeout, port=port)
    except errors.SSHError:
        output += 'Unable to connect to port %s on device: %s\n' % \
            (str(port), ip)
    except errors.AuthenticationError:  # NCClient auth failure
        output += 'Authentication failure for device: %s\n' % ip
    except AuthenticationException:  # Paramiko auth failure
        output += 'Authentication failure for device: %s\n' % ip
    except SSHException as e:
        output += 'Error connecting to device: %s\nError: %s' % (ip, str(e))
    except socket.timeout:
        output += 'Timeout exceeded connecting to device: %s\n' % ip
    except socket.error:
        output += 'The device refused the connection on port %s' % port
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
    return output


def commit(conn, cmds, commit_check, commit_confirm, commit_blank,
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
    @param commit_confirm: An integer of minutes that the user wants to
                         | commit confirm for.
    @type commit_confirm: int
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
            output += ("\nUncommitted changes left on the device or "
                       "someone else is in edit mode, couldn't lock the "
                       "candidate configuration.\n")
        except:
            output += ("Failed to commit check on device %s for an "
                       "unknown reason." % ip)
        else:
            # add the 'show | compare' output.
            output += "Compare results:\n" + conn.compare_config(cmds) + '\n'
            output += "\nCommit check results from: %s\n" % conn.host
            output += results
    # Actually commit the cmds.
    else:
        # add the 'show | compare' output.
        if not commit_blank:  # no results to show on blank commit.
            output += "Compare results:\n" + conn.compare_config(cmds) + '\n'
        if commit_confirm:
            output += ("Attempting to commit confirm on device: %s\n"
                       % conn.host)
        else:
            output += "Attempting to commit on device: %s\n\n" % conn.host
        try:
            output += conn.commit(commit_confirm=commit_confirm,
                                  comment=comment, at_time=at_time,
                                  synchronize=synchronize, commands=cmds)
        except RPCError as e:
            output += ('Commit could not be completed on this device, '
                       'due to the following error: \n' + str(e))
        # TODO: no Jaide-specific success/fail message, currently just dumping the output from the device.
        # if results:
        #     if results.find('commit-check-success') is None:  # None is returned for elements found without a subelement, as in this case.
        #         if commit_confirm:
        #             output += 'Commit complete on device: %s. It will be automatically rolled back in %s minutes, unless you commit again.\n' % (conn.host, str(commit_confirm))
        #         elif at_time:
        #             output += 'Commit staged to happen at %s on device: %s' % (at_time, conn.host)
        #         else:
        #             output += 'Commit complete on device: %s\n' % conn.host
        # else:
        #     output += 'Commit failed on device: %s\n' % conn.host
        #     # for each line in the resultant xml, iterate over and print out the non-empty lines.
        #     for i in results.findall('commit-results')[0].itertext():
        #         if i.strip() != '':
        #             output += '\n' + i.strip()
    return output


def dev_info(conn):
    """Get basic device information."""
    return '\n' + conn.dev_info()


def health_check(conn):
    """Get alarm and health information."""
    return '\n' + conn.health_check()


def int_errors(conn):
    """Get any interface errors from the device."""
    return '\n' + conn.int_errors()


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
        if shell:
            output += '\n> ' + cmd + conn.shell_cmd(cmd)
        else:
            xpath_expr = ''
            # Get xpath expression from the command, if it is there.
            # If there is an xpath expr, the output will be xml,
            # overriding the format parameter
            #
            # Example command forcing xpath: show route % //rt-entry
            if len(cmd.split('%')) == 2:
                op_cmd = cmd.split('%')[0] + '\n'
                xpath_expr = cmd.split('%')[1].strip()
            if xpath_expr:
                output += '\n> ' + cmd + \
                    conn.op_cmd(command=op_cmd, req_format='xml',
                                xpath_expr=xpath_expr) + '\n'
            else:
                output += '\n> ' + cmd + conn.op_cmd(cmd,
                                                     req_format=req_format)
    return output


def write_to_file(screen_output):
    """ Print the output to the user, or write it to file.

    Purpose: This function is called to either print the screen_output to
           | the user, or write it to a file
           | if we've received a filepath prepended on the output string in
           | between identifiers '*****WRITE_TO_FILE*****'

    @param screen_output: String containing all the output gathered.
    @type screen_output: str

    @returns: None
    """
    if "*****WRITE_TO_FILE*****" in screen_output:
        dest_file = screen_output.split('*****WRITE_TO_FILE*****')[1]
        style = screen_output.split('*****WRITE_TO_FILE*****')[2]
        screen_output = screen_output.split('*****WRITE_TO_FILE*****')[3]
        # open the output file if one was specified.
        if style.lower() in ["s", "single"]:
            try:
                out_file = open(dest_file, 'a+b')
            except IOError as e:
                print('Error opening output file \'%s\' for writing. Here is '
                      'the output that would\'ve been written:\n' % dest_file)
                print(screen_output)
                print('\n\nHere is the error for opening the output file:')
                raise e
            else:
                out_file.write('%s\n\n' % screen_output)
                print('\nOutput written/appended to: ' + dest_file)
        elif style.lower() in ["m", "multiple"]:
            # get the ip for the current device from the output.
            ip = screen_output.split('device: ')[1].split('\n')[0].strip()
            try:
                filepath = path.join(path.split(dest_file)[0], ip + "_" +
                                     path.split(dest_file)[1])
                out_file = open(filepath, 'a+b')
            except IOError as e:
                print('Error opening output file \'%s\' for writing. Here is '
                      'the output that would\'ve been written:\n' % dest_file)
                print(screen_output)
                print('\n\nHere is the error for opening the output file:')
                raise e
            else:
                out_file.write(screen_output)
                print('\nOutput written/appended to: ' + filepath)
                out_file.close()
    else:
        # --scp function copy_file will return '' if we aren't writing to a
        # file, because the output is printed to the user immediately.
        # Therefore we only need to print if something exists.
        print screen_output if screen_output else None

##########################
# Start of script proper #
##########################
if __name__ == '__main__':
    # Verify requirements.
    args = prs.parse_args()
    if args.scp and (args.scp[0].lower() not in ['pull', 'push']):
        prs.error('When using the --scp flag, you must specify the direction '
                  'as the first argument. For example: "--scp pull /var/tmp '
                  '/path/to/local/folder"')

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

    # Correlates argument with function pointer
    function_translation = {
        "command": multi_cmd,
        "commit_blank": commit,
        "int_error": int_errors,
        "health_check": health_check,
        "info": dev_info,
        "make_commit": commit,
        "shell": multi_cmd
    }
    # Correlates which params need to be passed through open_connection() to
    # the final function.
    args_translation = {
        "command": [args.command, False, args.format.lower()],
        "int_error": None,
        "health_check": None,
        "info": None,
        "make_commit":
            [args.make_commit, args.commit_check, args.commit_confirm,
                args.commit_blank, args.commit_comment, args.commit_at,
                args.commit_synchronize],
        "commit_blank":
            [args.make_commit, args.commit_check, args.commit_confirm,
                args.commit_blank, args.commit_comment, args.commit_at,
                args.commit_synchronize],
        "shell": [args.shell, True, args.sess_timeout]
    }

    # Compares args to function_translation to figure out which we are doing
    # then looks up the function pointer and arguments
    # vars(args) will convert the Namespace from argparser in to a dictionary
    # we can iterate over
    for key in vars(args).keys():
        if key in function_translation:
            if vars(args)[key] not in [None, False]:
                function = function_translation[key]
                argsToPass = args_translation[key]

    #################
    # START OF MODS #
    #################
    # Use # of CPU cores * 2 threads. Cpu_count usually returns double the
    # number of physical cores because of hyperthreading.
    mp_pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
    for ip in clean_lines(args.ip):
        write_to_file(open_connection(ip.strip(), args.username, args.password,
                                      function, argsToPass, args.write,
                                      args.conn_timeout, args.sess_timeout,
                                      args.port))
        # TODO: add in passing sess-timeout and port to open_connection
        # mp_pool.apply_async(open_connection,
        #                     args=(ip.strip(), args.username, args.password, function,
        #                           argsToPass, args.write, args.conn_timeout, args.sess_timeout, args.port),
        #                     callback=write_to_file)
    # mp_pool.close()
    # mp_pool.join()

    # iplist = ""
    # if len(args.ip.split(',')) > 1:  # Split the IP argument based on commas to see if there is more than one.
    #     iplist = args.ip.split(',')
    # elif path.isfile(args.ip):
    #     try:
    #         iplist = open(args.ip, 'rb')  # open the iplist in read only mode, the 'b' is for windows compatibility.
    #     except IOError as e:
    #         print('Couldn\'t open the IP list file %s due to the error:\n' % args.ip)
    #         raise e
    # if args.scp:
    #     # Needed something to let the user know we were starting.
    #     print ("Starting Copy...")
    # if iplist != "":  # We have matched for multiple IPs, and need to multiprocess.
    #     # Use # of CPU cores * 2 threads. Cpu_count usually returns double the # of physical cores because of hyperthreading.
    #     mp_pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
    #     for IP in iplist:
    #         IP = IP.strip()
    #         if IP != "" and IP[0] != '#':  # skip blank lines and comments
    #             if args.scp:  # scp is handled separately
    #                 mp_pool.apply_async(jaide.copy_file, args=(args.scp[1], args.scp[2], IP, args.username, args.password, args.scp[0], args.write, True, None), callback=jaide.write_output)
    #             else:
    #                 mp_pool.apply_async(jaide.do_netconf, args=(IP, args.username, args.password, function, argsToPass, args.write, args.timeout), callback=jaide.write_output)
    #     mp_pool.close()
    #     mp_pool.join()
    # else:  # args.ip should be one IP address, and no multiprocessing is required.
    #     if args.scp:
    #         if args.quiet:
    #             jaide.write_output(jaide.copy_file(args.scp[1], args.scp[2], args.ip, args.username, args.password, args.scp[0], args.write, False, None))
    #         else:
    #             jaide.write_output(jaide.copy_file(args.scp[1], args.scp[2], args.ip, args.username, args.password, args.scp[0], args.write, False, callback=jaide.copy_status))
    #     else:
    #         # the jaide.do_netconf() will return a string that is passed to the jaide.write_output() function for outputting to the user/file.
    #         jaide.write_output(jaide.do_netconf(ip=args.ip, username=args.username, password=args.password, function=function, args=argsToPass, write_to_file=args.write, timeout=args.timeout))
