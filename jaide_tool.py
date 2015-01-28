""" This is the cli script that is a base use case of the jaide module.
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
import argparse
import getpass
import re
import jaide

# -i is a required parameter, the rest are optional arguments
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description="Required Modules:\n\tNCCLIENT - https://github.com/leopoul/ncclient/ \n\tPARAMIKO - "
                                "https://github.com/paramiko/paramiko \n\tSCP - https://pypi.python.org/pypi/scp/ \n\tPyCrypto - http://www.voidspace.org.uk/python/modules.shtml#pycrypto"
                                "\n\nThis script can be used as an aide to easily do the same command(s) to multiple juniper devices. "
                                "The only required arguments are the destination IP address(es), and one of the following commands:\nSingle Format: "
                                "\t[ -c | -e | -H | -I | -s | -S | -l | -b ]\nName Format: \t[ --command | --errors | --health | --info | --set | --scp | --shell | --blank ]",
                                prog='jaide.py', usage="%(prog)s -i IP [-c [operational_mode_commands | file_of_operational_commands] | -e | -H | -I | -s"
                                " [set_commands | file_of_set_commands] | -S [push | pull] source destination | -l [shell_commands | file_of_shell_commands] | -b]")
parser.add_argument("-i", "--ip", required=True, dest='ip', type=str, help="The target device(s) to run the script against. This can be a single target device IP address, "
                    "a quoted comma separated list of IP's, or a filepath to a file containing IP's on each line. DNS resolution will work using your machine's specified DNS server.")
parser.add_argument("-u", "--username", dest='username', type=str, default='default', help="Username  -  Will prompt if not specified.")
parser.add_argument("-p", "--password", dest='password', type=str, default='default', help="Password  -  Will prompt if not specified.")
parser.add_argument("-w", "--write", dest='write', metavar=("[s/single | m/multiple]", "OUTPUT_FILENAME"), nargs=2, type=str, help="Specify a filename to write all script "
                    "output. Also requires whether to write to a single file or a separate file per IP. (ex. -w s ~/Desktop/output.txt). The output format for the names of multiple files is IP_OUTPUTFILENAME.")
parser.add_argument("-q", "--quiet", dest='quiet', action="store_true", help="Can be used with --scp when copying to/from a single device to prevent seeing the live "
                    "status of the transfer. Might be useful when transmitting a large number of files/folders.")
parser.add_argument("-t", "--timeout", dest="timeout", type=int, default=300, help="Specify the timeout value for the NCClient connection, in seconds."
                    " Default is 300 seconds. This should be increased when no output could be seen for more than 5 minutes (ex. requesting a system snapshot).")
parser.add_argument("-f", "--format", dest="format", type=str, default='text', metavar='[ text | xml ]', help="Formats output to text or xml. Should be used with -c."
                    " Default format is text. Including an xpath expression after a command forces XML output (EX. \"show route %% //rt-entry\").")

# Script functions: Must select one and only one.
group1 = parser.add_mutually_exclusive_group(required=True)
group1.add_argument("-c", "--command", dest='command', metavar="[operational_mode_commands | file_of_operational_commands]", type=str, help="Send a single operational"
                    " mode command to device(s). A trailing '%%' followed by an xpath expression will filter the xml results by that expression. For example: 'show route %% //rt-entry'")
group1.add_argument("-e", "--errors", dest='int_error', action='store_true', help='Check all interfaces for errors.')
group1.add_argument("-H", "--health", dest="health_check", action="store_true", help="Grab a Health Check: CPU/Mem usage, alarms, etc from device.")
group1.add_argument("-I", "--info", dest='info', action='store_true', help="Get basic device info (Serial #, Model, etc).")
group1.add_argument("-s", "--set", dest='make_commit', metavar="[set_commands | file_of_set_commands]", type=str, help="Send and commit set command(s) to device(s). "
                    "Can be a single quoted command, a quoted comma separated list of commands, or a file with a list of set commands on each line. "
                    "Can be used with the commit options --check, --confirm, --blank, --comment, --synchronize, and --at.")
group1.add_argument("-S", "--scp", nargs=3, dest="scp", type=str, metavar=("[push | pull]", "source", "destination"), help="The SCP argument -S expects three arguments."
                    " In order, they are the direction 'push' or 'pull', the source file/folder, and the destination file/folder."
                    " For example, this could be used to pull a directory using '--scp pull /var/tmp /path/to/local/destination'")
group1.add_argument("-l", "--shell", dest='shell', metavar="[shell_commands | file_of_shell_commands]", type=str, help="Similar to -c, except it will run the commands from "
                    "shell instead of operational mode.")
group1.add_argument("-b", "--blank", dest="commit_blank", action='store_true', help="Can be used with or without -s to make a blank commit. A key use case is when trying"
                    " to confirm a commit confirm. --confirm, --check, --blank, and --at are mutually exclusive!")

# Commit options. These options are mutually exclusive.
group2 = parser.add_mutually_exclusive_group()
group2.add_argument("-m", "--confirm", dest='commit_confirm', metavar="CONFIRM_MINUTES", type=int, choices=range(1, 61), help="Can be used with -s to make a confirmed commit. "
                    "Accepts a number in /minutes/ between 1 and 60! --confirm, --check, --blank, and --at are mutually exclusive!")
group2.add_argument("-k", "--check", dest="commit_check", action='store_true', help="Can be used with -s to only run a commit check, and not commit the changes."
                    " --confirm, --check, --blank, and --at are mutually exclusive!")
group2.add_argument("-a", "--at", dest='commit_at', type=str, metavar="COMMIT_AT_TIME", help="Specify a time for the device to make the commit at. Junos expects one of two formats: "
                    "A time value of the form 'hh:mm[:ss]' or a date and time value of the form 'yyyy-mm-dd hh:mm[:ss]' (seconds are optional).")

# Inclusive commit options that can be used with each other and the other mutually exclusive options.
group3 = parser.add_argument_group('Inclusive Commit Options', 'Unlike the other mutually exclusive commit options, '
                                   'these options below can be used with each other or together with any other commit option.')
group3.add_argument('-C', '--comment', dest="commit_comment", type=str, help="Add a comment to the commit that will be written to the commit log. This should be a quoted string.")
group3.add_argument('-y', '--synchronize', dest="commit_synchronize", action='store_true', help="Enforce a commit synchronize operation.")

##########################
# Start of script proper #
##########################
if __name__ == '__main__':
    # Verify requirements.
    args = parser.parse_args()
    if args.scp and (args.scp[0].lower() != 'pull' and args.scp[0].lower() != 'push'):
        parser.error('When using the --scp flag, you must specify the direction as the first argument. For example: "--scp pull /var/tmp /path/to/local/folder"')

    # if they are doing commit_at, ensure the input is formatted correctly.
    if args.commit_at:
        if re.search(r'([0-2]\d)(:[0-5]\d){1,2}', args.commit_at) is None and re.search(r'\d{4}-[01]\d-[0-3]\d [0-2]\d:[0-5]\d(:[0-5]\d)?', args.commit_at) is None:
            raise BaseException("The specified commit at time is not in one of the two following formats:\nA time value of the form 'hh:mm[:ss]'\n"
                "A date and time value of the form 'yyyy-mm-dd hh:mm[:ss]' (seconds are optional).")

    # Check if the username and password are the defaults.
    # If they are, we'll prompt the user for them.
    if args.username == 'default':
        args.username = raw_input("Username: ")
    if args.password == 'default':
        # getpass will not echo back to the user, for safe password entry.
        args.password = getpass.getpass()

    # Correlates argument with function pointer
    function_translation = {
        "command": jaide.multi_cmd,
        "commit_blank": jaide.make_commit,
        "int_error": jaide.int_errors,
        "health_check": jaide.health_check,
        "info": jaide.dev_info,
        "make_commit": jaide.make_commit,
        "shell": jaide.multi_cmd
    }
    # Correlates which args need to be sent to jaide.do_netconf based on which
    # feature is being used. Must be enclosed in brackets, otherwise
    # argument unpacking will mess it up
    args_translation = {
        "command": [args.command, False, args.format.lower(), args.timeout],
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

        "shell": [args.shell, True, args.timeout]
    }

    # Compares args to function_translation to figure out which we are doing
    # then looks up the function pointer and arguments
    # vars(args) will convert the Namespace from argparser in to a dictionary
    # we can iterate over
    for key in vars(args).keys():
        if key in function_translation:
            if vars(args)[key] is not None and vars(args)[key] is not False:
                function = function_translation[key]
                argsToPass = args_translation[key]

    iplist = ""
    if len(args.ip.split(',')) > 1:  # Split the IP argument based on commas to see if there is more than one.
        iplist = args.ip.split(',')
    elif path.isfile(args.ip):
        try:
            iplist = open(args.ip, 'rb')  # open the iplist in read only mode, the 'b' is for windows compatibility.
        except IOError as e:
            print('Couldn\'t open the IP list file %s due to the error:\n' % args.ip)
            raise e
    if args.scp:
        # Needed something to let the user know we were starting.
        print ("Starting Copy...")
    if iplist != "":  # We have matched for multiple IPs, and need to multiprocess.
        # Use # of CPU cores * 2 threads. Cpu_count usually returns double the # of physical cores because of hyperthreading.
        mp_pool = multiprocessing.Pool(multiprocessing.cpu_count() * 2)
        for IP in iplist:
            IP = IP.strip()
            if IP != "" and IP[0] != '#':  # skip blank lines and comments
                if args.scp:  # scp is handled separately
                    mp_pool.apply_async(jaide.copy_file, args=(args.scp[1], args.scp[2], IP, args.username, args.password, args.scp[0], args.write, True, None), callback=jaide.write_output)
                else:
                    mp_pool.apply_async(jaide.do_netconf, args=(IP, args.username, args.password, function, argsToPass, args.write, args.timeout), callback=jaide.write_output)
        mp_pool.close()
        mp_pool.join()
    else:  # args.ip should be one IP address, and no multiprocessing is required.
        if args.scp:
            if args.quiet:
                jaide.write_output(jaide.copy_file(args.scp[1], args.scp[2], args.ip, args.username, args.password, args.scp[0], args.write, False, None))
            else:
                jaide.write_output(jaide.copy_file(args.scp[1], args.scp[2], args.ip, args.username, args.password, args.scp[0], args.write, False, callback=jaide.copy_status))
        else:
            # the jaide.do_netconf() will return a string that is passed to the jaide.write_output() function for outputting to the user/file.
            jaide.write_output(jaide.do_netconf(ip=args.ip, username=args.username, password=args.password, function=function, args=argsToPass, write_to_file=args.write, timeout=args.timeout))
