from jaide import Jaide

session = Jaide('172.25.1.21', 'operate', 'Op3r4t3')

# commands = '/Users/nprintz/Desktop/oplist.txt'
# for cmd in Jaide.iter_cmds(commands):
#     print session.op_cmd(cmd)

# print session.op_cmd(command='show interfaces terse | match lo0')
print session.compare_config(commands=['set interfaces ge-0/0/0 description asdopfireio','set interfaces ge-0/0/1 description asdf'])
# print session.commit_check(commands='set interfaces ge-0/0/0 description qweqweqweqwe')
# print session.commit(commands='set interfaces ge-0/0/0 description qweqweqweqwe', comment="test commit", commit_confirm=10)
# print session.compare_config()

# commands = " # op commands, show interfaces terse, show version,\n, \n,show system commit"
# for cmd in Jaide.iter_cmds(commands):
#     print cmd

session.disconnect()
