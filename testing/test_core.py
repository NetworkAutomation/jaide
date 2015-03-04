""" Test script for core Jaide Class. """

from jaide import Jaide
from jaide.color_utils import color
from jaide.utils import clean_lines
import cProfile
import socket
import click
import os


def op_commands(session, op_list):
    # Try a single op command
    print color('Single op command: show interfaces terse | match lo0', 'info')
    print session.op_cmd('show interfaces terse | match lo0')

    # single op command with xml output
    print color('Single op command in xml format: show interfaces terse | match lo0', 'info')
    print session.op_cmd('show interfaces terse | match lo0', req_format='xml')

    # single op command with xpath filtering
    print color('Single op command with xpath filtering on package-information: show version', 'info')
    print session.op_cmd('show version', xpath_expr='//package-information')

    # Try a list of op commands, includes the following:
    #     regular command
    #     show version
    #     # command with piping
    #     show route | match 0.0.0.0
    print color('Multiple op commands from file:', 'info')
    # loop over the commands in our file
    for cmd in clean_lines(op_list):
        print color(cmd, 'info')
        print session.op_cmd(cmd)


def shell_commands(session, shell_list):
    # try a single shell command
    print color('Single shell command: pwd', 'info')
    print session.shell_cmd('pwd')

    # try a shell command file
    # file contents:
    #    pwd
    #    cd /var/tmp
    #    pwd
    #    ls -lap
    #    touch my-new-file
    #    ls -lap
    print color('multiple shell commands from file:', 'info')
    # loop over the commands in our file.
    for cmd in clean_lines(shell_list):
        print color(cmd, 'info')
        print session.shell_cmd(cmd)


def conn_timeout_test(host):
    try:
        Jaide(host, 'asdf', '123', connect_timeout=10)
    except socket.timeout:
        print color('The connection failed, as expected')
        return True
    print color('The connection did not fail, check settings for this test.', 'error')


def commit_check_test(session, set_list):
    print session.commit_check(set_list)


def compare_config_test(session, set_list):
    print session.compare_config(set_list)


def commit_tests(session):
    print color('Starting commit log', 'info')
    print session.op_cmd('show system commit')

    print color('Attempting blank commit:', 'info')
    print session.commit()

    print color('Attempting blank commit with comment:', 'info')
    print session.commit(comment="blank with comment")

    print color('Attempting blank commit with comment and synchronize:', 'info')
    print session.commit(comment="blank with comment and synch", synchronize=True)

    print color('Attempting blank commit confirmed for 20 minutes:', 'info')
    print session.commit(confirmed=1200)

    print color('Attempting to confirm the commit confirmed:', 'info')
    print session.commit()

    print color('Attempting to commit at:', 'info')
    print session.commit(at_time='23:59')

    print color('Ending commit Log:', 'info')
    print session.op_cmd('show system commit')
    print session.op_cmd('clear system commit')


def config_diff_test(session, second_host):
    for output in session.diff_config(second_host):
        print output


def scp_tests(session, remote_dir, local_dir, remote_file, local_file):
    print color('Copying a single file TO device', 'info')
    print session.scp_push(local_file, remote_dir, True)
    session.shell_cmd('rm %s/%s' % (remote_dir, os.path.basename(local_file)))

    print color('Copying a single file FROM device', 'info')
    print session.scp_pull(remote_file, local_dir + '/', True)

    print color('Copying a directory TO device', 'info')
    print session.scp_push(local_dir, remote_dir, True)
    session.shell_cmd('rm -R %s/%s' % (remote_dir, os.path.basename(local_dir)))

    print color('Copying a directory FROM device', 'info')
    print session.scp_pull(remote_dir, local_dir, True)

# needed for '-h' to be a help option
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.command(context_settings=CONTEXT_SETTINGS,
               help="Run the test suite. Warning: Several commits will be made!")
@click.option('-i', '--host', prompt='First host')
@click.option('-u', '--username', prompt='First host username')
@click.password_option('-p', '--password', prompt='First host password', confirmation_prompt=False)
@click.option('-I', '--second-host', prompt='Second host for root account')
@click.password_option('-P', '--second-password', prompt='Second password for root account', confirmation_prompt=False)
@click.option('-H', '--third-host', prompt='Third host that doesn\'t exist')
@click.option('-D', '--remote-dir', prompt="Directory on remote device",
              type=click.Path(file_okay=False))
@click.option('-d', '--local-dir', prompt="Directory on local device",
              type=click.Path(exists=True, file_okay=False, writable=True,
                              resolve_path=True))
@click.option('-F', '--remote-file', prompt="File on remote device",
              type=click.Path(dir_okay=False))
@click.option('-f', '--local-file', prompt="File on local device",
              type=click.Path(exists=True, dir_okay=False, writable=True,
                              resolve_path=True))
@click.option('-s', '--set-list', prompt="File of set commands",
              type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('-o', '--op-list', prompt="file of operational commands",
              type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('-S', '--shell-list', prompt="file of shell commands",
              type=click.Path(exists=True, dir_okay=False, resolve_path=True))
def main(host, username, password, second_host, second_password, third_host,
         remote_dir, local_dir, remote_file, local_file, set_list, op_list,
         shell_list):
    # open connection
    print color('Connecting to %s with %s / %s' % (host, username, password), 'info')
    session = Jaide(host, username, password)

    # test op and shell commands
    print color('Testing op commands', 'info')
    op_commands(session, op_list)
    print color('Testing shell commands', 'info')
    shell_commands(session, shell_list)

    # disconnect, change username/password/host, and do the commands again
    print color('Disconnecting first session', 'info')
    session.disconnect()

    # changing to the root user will test other use case of migration from
    # shell to cli on initialization of the connection
    print color('\nChanging parameters to root:%s@%s' % (second_password, second_host), 'info')
    session.username = 'root'
    session.password = second_password
    session.host = second_host

    print color('Testing op commands', 'info')
    op_commands(session, op_list)
    print color('Testing shell commands', 'info')
    shell_commands(session, shell_list)

    # scp tests here
    print color('Testing SCP operations', 'info')
    scp_tests(session, remote_dir, local_dir, remote_file, local_file)

    print color('\nTesting modifying conn_timeout to 10 seconds connection that will fail:', 'info')
    print color('the method \'connect\' should clock total time of 10 seconds:', 'info')
    cProfile.runctx('conn_timeout_test(host)', globals(), {'host': third_host})

    print color('Disconnecting session again.', 'info')
    session.disconnect()

    # change back to non-root user for speed of tests.
    print color('\nChanging parameters to operate:Op3r4t3@172.25.1.21', 'info')
    session.username = username
    session.password = password
    session.host = host

    # config diff test
    print color('Performing a config diff:', 'info')
    config_diff_test(session, second_host)

    # commit check test
    print color('Performing a commit check:', 'info')
    commit_check_test(session, set_list)

    # show | compare test
    print color('Performing a commit compare:', 'info')
    compare_config_test(session, set_list)

    # commit option tests
    print color('Performing commit tests:', 'info')
    commit_tests(session)

    # change session timeout
    print color('changing timeout to 1 second and doing an RSI, which should timeout', 'info')
    session.session_timeout = 1
    try:
        print session.op_cmd('request support information')
    except socket.timeout:
        print color('Timeout exceeded as expected')

    # print color('trying a shell command to timeout', 'info')
    # try:
    #     print session.shell_cmd('scp /var/tmp/gimp-2.8.14.dmg /var/tmp/gimp-copy')
    # except socket.timeout:
    #     print color('Timeout exceeded as expected.')

    session.disconnect()

if __name__ == '__main__':
    main()
