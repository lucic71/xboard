from cmd import Cmd
from subprocess import Popen, PIPE
import argparse
import datetime
import traceback
import os
import sys
import sidefun
import readline
import loadcfg
import subprocess
import getpass
from collections import defaultdict

import warnings
warnings.filterwarnings(action='ignore', module=".*paramiko.*")

histfile = os.path.expanduser('~/xboard/.xboard.history')
histfile_size = 1000

class xBoard(Cmd):

    # Prompt for shell tool
    prompt = 'x>> '

    # When paramiko throws the output back to this script the prompt
    # 'system> ' is also included. So I will replace it in order to have
    # a cleaner output
    systemPrompt = 'system> '

    # Initial servers info
    servers = loadcfg.loadcfg()

    #List of servers which are powered off
    off = defaultdict(list)
    off.fromkeys(['server', 'user', 'password', 'port'])



    # Keep track of command history using preloop
    # and postloop functions
    def preloop(self):
        if readline and os.path.exists(histfile):
            readline.read_history_file(histfile)

    def postloop(self):
        if readline:
            readline.set_history_length(histfile_size)
            readline.write_history_file(histfile)
    ########

    def do_addserver(self, inp):
        """Configure the settings for adding a new server. Options:
            -wf Add furthermore the server in xboard.cfg"""
        server = input("Server: ")
        user = input("User: ")
        port = input("Port: ")
        password = getpass.getpass("Password: ")

        # Remove whitespaces

        server = server.replace(" ", "")
        user = user.replace(" ", "")
        user = user.replace(" ", "")
        password = password.replace(" ", "")

        self.servers['server'].append(server)
        self.servers['user'].append(user)
        self.servers['port'].append(port)
        self.servers['password'].append(password)

        if inp == '-wf':
            with open('xboard.cfg', 'a+') as configFile:
                line = ','.join([server, user, password, port])
                configFile.write(line + '\n')

    def do_refill(self, inp):
        "Refills the list of initial servers"
        self.servers = loadcfg.loadcfg()
        self.do_ls(inp)
        print("Servers list was refilled!")


    def do_checkup(self, inp):
        """Check if servers are up using nc tool. Options:
            -t set timeout for listening. Default is 10"""

        # Set timeout
        timeout = 10;
        if inp:
            timeout = int(agrs[1])

        # List of servers which are down
        unavailable = defaultdict(list)
        unavailable.fromkeys(['server', 'user', 'password', 'port'])

        serverLength = len(self.servers['server'])

        # Used for writing date and time info in file
        infocount = 0

        for i in range(0, serverLength):

            commandfull = 'nc -v -w %d %s -z 22' % (timeout, \
                    self.servers['server'][i])

            commandlist = commandfull.split(' ')

            checkProcess = Popen(commandlist, stdout=PIPE, stderr=PIPE)

            # Apparently nc flushes all output to stderr
            stdout, stderr = checkProcess.communicate()
            stderr = stderr.decode('utf-8')

            # Fill a dictionary with servers which are down
            if "succeeded" not in stderr:

                print('Server %s will be removed from servers list!' % \
                        self.servers['server'][i])

                with open('xboard.log', 'a+') as log:
                    now = datetime.datetime.now()

                    # Write info about date and time just at the first line
                    # of local block of data

                    if infocount == 0:
                        log.write('Informations about checkup at %s\n' % \
                                now.strftime("%Y-%m-%d %H:%M"))
                        infocount = 1
                    log.write(stderr)

                unavailable['server'].append(self.servers['server'][i])
                unavailable['user'].append(self.servers['user'][i])
                unavailable['password'].append(self.servers['password'][i])
                unavailable['port'].append(self.servers['port'][i])

            else:
                print(stderr, end='')

                # power status
                checkPower = sidefun.powerstatus(self.servers['server'][i], \
                        self.servers['user'][i], self.servers['password'][i], \
                        self.servers['port'][i])

                if 'on' not in checkPower:
                    print("Server's power state is off!")

                    self.off['server'].append(self.servers['server'][i])
                    self.off['user'].append(self.servers['user'][i])
                    self.off['password'].append(self.servers['password'][i])
                    self.off['port'].append(self.servers['port'][i])


        ####### Print servers which are unavailable
        if unavailable:
            print("\nList of down servers:")
            for i in range(0, len(unavailable['server'])):
                    print(unavailable['server'][i], unavailable['port'][i])
                    self.servers['server'].remove(unavailable['server'][i])
                    self.servers['user'].remove(unavailable['user'][i])
                    self.servers['password'].remove(unavailable['password'][i])
                    self.servers['port'].remove(unavailable['port'][i])

        ####### Print servers which are off
        if self.off:
            print("\nList of powered off servers:")
            for i in range(0, len(self.off['server'])):
                    print(self.off['server'][i], self.off['port'][i])

                    # Maybe remove will fail because the server is already
                    # removed from self.servers['server'] list so a try-except
                    # block is useful here

                    try:
                        self.servers['server'].remove(self.off['server'][i])
                        self.servers['user'].remove(self.off['user'][i])
                        self.servers['password'].remove(self.off['password'][i])
                        self.servers['port'].remove(self.off['port'][i])
                    except:
                        pass

            print("Do you want to power on this servers?" + '\n')
            confirm = input("Y/n: ")
            if confirm is 'Y' or confirm is 'y':
                for i in range(len(self.off['server'])):
                    sidefun.poweron(self.off['server'][i], \
                            self.off['user'][i], self.off['password'][i], \
                            self.off['port'][i])


            print("Check xboard.log for more info about checkup using 'log' command!")
        elif not unavailable and self.servers['server']:
            print("\nAll servers are up!")



    def do_select(self, option):
        # TODO check index range
        """options:
            -out  exclude a server or a list of servers separated by commas
            -outn exclude first n servers from servers list
            -outN exclude last N servers from servers list
            -r    delete all servers excluding a given server or a list of servers
            """
        args = option.split()

        # If out option has no arguments
        if len(args) == 1 and args[0] == '-out' :
            print("You must include servers to be ignored from servers list!")
            return


        if len(args) > 3:
            print("Error: too many arguments. See '? select'")
            return

        # Config for out option
        if len(args) == 2 and args[0] == '-out':

            serverList = args[1].split(',')
            for serverToDelete in serverList:

                if "*" in serverToDelete:
                    search = serverToDelete.split('*')
                    # String starts with text preceded by *
                    if search[1] == '':
                        indexes = [i for i in range(len(self.servers['server']))\
                                if self.servers['server'][i].startswith(search[0])]

                    # String ends with text succeeded by *
                    elif search[0] == '':
                        indexes = [i for i in range(len(self.servers['server']))\
                                if self.servers['server'][i].endswith(search[1])]

                    # * is in the middle of the string
                    elif search[0] != '' and search[1] != '':
                        indexes = [i for i in range(len(self.servers['server'])) if \
                                search[0] in self.servers['server'][i] and search[1] \
                                in self.servers['server'][i]]

                elif "*" not in serverToDelete:
                    indexes = [i for i in range(len(self.servers['server'])) \
                            if self.servers['server'][i] == serverToDelete]

                if not indexes:
                    print("Server not found!")
                    return

                for index in sorted(indexes, reverse=True):
                    del self.servers['server'][index]
                    del self.servers['password'][index]
                    del self.servers['user'][index]
                    del self.servers['port'][index]

            return

        if len(args) == 2 and args[0] == '-outn':
            indexes = []
            for i in range(int(args[1])):
                indexes.append(i)

            for index in sorted(indexes, reverse=True):
                del self.servers['server'][index]
                del self.servers['password'][index]
                del self.servers['user'][index]
                del self.servers['port'][index]

            return

        if len(args) == 2 and args[0] == '-outN':
            indexes = []

            for i in range(len(self.servers['server']) - int(args[1]), \
                    len(self.servers['server'])):
                indexes.append(i)

            for index in sorted(indexes, reverse=True):
                del self.servers['server'][index]
                del self.servers['password'][index]
                del self.servers['user'][index]
                del self.servers['port'][index]

            return

        if len(args) == 2 and args[0] == '-r':

            serverList = args[1].split(',')
            for serverToDelete in serverList:

                if "*" in serverToDelete:
                    search = serverToDelete.split('*')
                    # String starts with text preceded by *
                    if search[1] == '':
                        indexes = [i for i in range(len(self.servers['server']))\
                                if self.servers['server'][i].startswith(search[0])]

                    # String ends with text succeeded by *
                    elif search[0] == '':
                        indexes = [i for i in range(len(self.servers['server']))\
                                if self.servers['server'][i].endswith(search[1])]

                    # * is in the middle of the string
                    elif search[0] != '' and search[1] != '':
                        indexes = [i for i in range(len(self.servers['server'])) if \
                                search[0] in self.servers['server'][i] and search[1] \
                                in self.servers['server'][i]]

                elif "*" not in serverToDelete:
                    indexes = [i for i in range(len(self.servers['server'])) \
                            if self.servers['server'][i] == serverToDelete]


                # Calculate complement of indexes list
                allindexes = []
                for i in range(len(self.servers['server'])):
                    allindexes.append(i)

                indexes = set(allindexes) - set(indexes)

                if not indexes:
                    print("Server not found!")
                    return

                for index in sorted(indexes, reverse=True):
                    del self.servers['server'][index]
                    del self.servers['password'][index]
                    del self.servers['user'][index]
                    del self.servers['port'][index]

            return


        print("Error: unknown arguments. See '? select'")

    def do_nums(self, inp):
        "Print how many servers are available"
        print(len(self.servers['server']))

    def do_fans(self, options):
        "Get information about fans from every server"

        self.do_checkup(None)

        # List of servers from do_conn function
        ssh = sidefun.connect(self.servers)

        argv = options.split(' ')

        # If -f option is passed write to xboard.log and return
        if argv[0] == '-f':
            sidefun.filewrite('fans', ssh, self.servers)
            return

        # If an unknown option is passed display an error message and
        # return
        elif argv[0] != '-f' and argv[0] != '':
            print("Error: Unknown argument '%s' for command fans!" % argv[0])
            return

        sshLength = len(ssh)

        print('\n')

        # Go through the list and execute the command for
        # every server
        for i in range(0, sshLength):
            ssh_stdin, ssh_stdout, ssh_stderr = ssh[i].exec_command('fans')
            for lineout in ssh_stdout.read().splitlines():
                print(lineout.decode('utf-8').replace(systemPropmt, ''))
            for linerr in ssh_stderr.read().splitlines():
                print ('%s at %s on port %s' % (linerr.decode('utf-8').replace(systemPrompt, ''), \
                        self.servers['server'][i], self.servers['port'][i]))

            ssh[i].close()


    def do_led(self, options):
        "Get information about leds from every server"

        self.do_checkup(None)

        # List of servers from do_conn function
        ssh = sidefun.connect(self.servers)

        argv = options.split(' ')

        # If -f option is passed write to xboard.log and return
        if argv[0] == '-f':
            sidefun.filewrite('led', ssh, self.servers)
            return

        # If an unknown option is passed display an error message and
        # return
        elif argv[0] != '-f' and argv[0] != '':
            print("Error: Unknown argument '%s' for command led!" % argv[0])
            return

        sshLength = len(ssh)

        # Go through the list and execute the command for
        # every server
        for i in range(0, sshLength):
            ssh_stdin, ssh_stdout, ssh_stderr = ssh[i].exec_command('led')
            for line in ssh_stdout.read().splitlines():
                print(line.decode('utf-8').replace(systemPrompt, ''))
            for linerr in ssh_stderr.read().splitlines():
                print ('%s at %s on port %s' % (linerr.decode('utf-8').replace(systemPrompt, ''), \
                        self.servers['server'][i], self.servers['port'][i]))

            ssh[i].close()


    def do_volts(self, options):
        "Get information about voltages from every server"

        self.do_checkup(None)

        # List of servers from do_conn function
        ssh = sidefun.connect(self.servers)

        argv = options.split(' ')

        # If -f option is passed write to xboard.log and return
        if argv[0] == '-f':
            sidefun.filewrite('volts', ssh, self.servers)
            return

        # If an unknown option is passed display an error message and
        # return
        elif argv[0] != '-f' and argv[0] != '':
            print("Error: Unknown argument '%s' for command volts!" % argv[0])
            return

        sshLength = len(ssh)

        # Go through the list and execute the command for
        # every server
        for i in range(0, sshLength):
            ssh_stdin, ssh_stdout, ssh_stderr = ssh[i].exec_command('volts')
            for line in ssh_stdout.read().splitlines():
                print(line.decode('utf-8').replace(systemPrompt, ''))
            for linerr in ssh_stderr.read().splitlines():
                print ('%s at %s on port %s' % (linerr.decode('utf-8').replace(systemPrompt, ''), \
                        self.servers['server'][i], self.servers['port'][i]))

            ssh[i].close()


    def do_temps(self, options):
        "Get information about temperature of every server"

        self.do_checkup(None)

        # List of servers from do_conn function
        ssh = sidefun.connect(self.servers)

        argv = options.split(' ')

        # If -f option is passed write to xboard.log and return
        if argv[0] == '-f':
            sidefun.filewrite('temps', ssh, self.servers)
            return

        # If an unknown option is passed display an error message and
        # return
        elif argv[0] != '-f' and argv[0] != '':
            print("Error: Unknown argument '%s' for command temps!" % argv[0])
            return

        sshLength = len(ssh)

        # Go through the list and execute the command for
        # every server
        for i in range(0, sshLength):
            ssh_stdin, ssh_stdout, ssh_stderr = ssh[i].exec_command('temps')
            for line in ssh_stdout.read().splitlines():
                print(line.decode('utf-8').replace(systemPrompt, ''))
            for linerr in ssh_stderr.read().splitlines():
                print ('%s at %s on port %s' % (linerr.decode('utf-8').replace(systemPrompt, ''), \
                        self.servers['server'][i], self.servers['port'][i]))

            ssh[i].close()

    def do_adapter(self, options):
        "Get information about adapters from every server"

        self.do_checkup(None)

        # List of servers from do_conn function
        ssh = sidefun.connect(self.servers)

        argv = options.split(' ')

        # If -f option is passed write to xboard.log and return
        if argv[0] == '-f':
            sidefun.filewrite('adapter', ssh, self.servers)
            return

        # If an unknown option is passed display an error message and
        # return
        elif argv[0] != '-f' and argv[0] != '':
            print("Error: Unknown argument '%s' for command adapter!" % argv[0])
            return

        sshLength = len(ssh)

        # Go through the list and execute the command for
        # every server
        for i in range(0, sshLength):
            ssh_stdin, ssh_stdout, ssh_stderr = ssh[i].exec_command('adapter')
            for line in ssh_stdout.read().splitlines():
                print(line.decode('utf-8').replace(systemPrompt, ''))
            for linerr in ssh_stderr.read().splitlines():
                print ('%s at %s on port %s' % (linerr.decode('utf-8').replace(systemPrompt, ''), \
                        self.servers['server'][i], self.servers['port'][i]))

            ssh[i].close()

    def do_fw(self, options):
        "Get information about Vital Product Data for every server"

        self.do_checkup(None)

        # List of servers from do_conn function
        ssh = sidefun.connect(self.servers)

        argv = options.split(' ')

        # If -f option is passed write to xboard.log and return
        if argv[0] == '-f':
            sidefun.filewrite('fw', ssh, self.servers)
            return

        # If an unknown option is passed display an error message and
        # return
        elif argv[0] != '-f' and argv[0] != '':
            print("Error: Unknown argument '%s' for command fw!" % argv[0])
            return

        sshLength = len(ssh)

        # Go through the list and execute the command for
        # every server
        for i in range(0, sshLength):
            ssh_stdin, ssh_stdout, ssh_stderr = ssh[i].exec_command('vpd fw')
            for line in ssh_stdout.read().splitlines():
                print(line.decode('utf-8').replace(self.systemPrompt, ''))
            for linerr in ssh_stderr.read().splitlines():
                print ('%s at %s on port %s' % (linerr.decode('utf-8').replace(self.systemPrompt, ''), \
                        self.servers['server'][i], self.servers['port'][i]))

            ssh[i].close()

    def do_imm(self, options):
        "Get information about Vital Product Data for every server"

        self.do_checkup(None)

        # List of servers from do_conn function
        ssh = sidefun.connect(self.servers)

        argv = options.split(' ')

        # If -f option is passed write to xboard.log and return
        if argv[0] == '-f':
            sidefun.filewrite('imm', ssh, self.servers)
            return

        # If an unknown option is passed display an error message and
        # return
        elif argv[0] != '-f' and argv[0] != '':
            print("Error: Unknown argument '%s' for command imm!" % argv[0])
            return

        sshLength = len(ssh)

        # Go through the list and execute the command for
        # every server
        for i in range(0, sshLength):
            ssh_stdin, ssh_stdout, ssh_stderr = ssh[i].exec_command('vpd imm')
            for line in ssh_stdout.read().splitlines():
                print(line.decode('utf-8').replace(systemPrompt, ''))
            for linerr in ssh_stderr.read().splitlines():
                print ('%s at %s on port %s' % (linerr.decode('utf-8').replace(systemPrompt, ''), \
                        self.servers['server'][i], self.servers['port'][i]))

            ssh[i].close()

    def do_sys(self, options):
        "Get information about Vital Product Data for every server"

        self.do_checkup(None)

        # List of servers from do_conn function
        ssh = sidefun.connect(self.servers)

        argv = options.split(' ')

        # If -f option is passed write to xboard.log and return
        if argv[0] == '-f':
            sidefun.filewrite('sys', ssh, self.servers)
            return

        # If an unknown option is passed display an error message and
        # return
        elif argv[0] != '-f' and argv[0] != '':
            print("Error: Unknown argument '%s' for command sys!" % argv[0])
            return

        sshLength = len(ssh)

        # Go through the list and execute the command for
        # every server
        for i in range(0, sshLength):
            ssh_stdin, ssh_stdout, ssh_stderr = ssh[i].exec_command('vpd sys')
            for line in ssh_stdout.read().splitlines():
                print(line.decode('utf-8').replace(self.systemPrompt, ''))
            for linerr in ssh_stderr.read().splitlines():
                print ('%s at %s on port %s' % (linerr.decode('utf-8').replace(self.systemPrompt, ''), \
                        self.servers['server'][i], self.servers['port'][i]))

            ssh[i].close()

    def do_dns(self, options):
        "Get information about dns for every server"

        self.do_checkup(None)

        # List of servers from do_conn function
        ssh = sidefun.connect(self.servers)

        argv = options.split(' ')

        # If -f option is passed write to xboard.log and return
        if argv[0] == '-f':
            sidefun.filewrite('dns', ssh, self.servers)
            return

        # If an unknown option is passed display an error message and
        # return
        elif argv[0] != '-f' and argv[0] != '':
            print("Error: Unknown argument '%s' for command dns!" % argv[0])
            return

        sshLength = len(ssh)

        # Go through the list and execute the command for
        # every server
        for i in range(0, sshLength):
            ssh_stdin, ssh_stdout, ssh_stderr = ssh[i].exec_command('dns')
            for line in ssh_stdout.read().splitlines():
                print(line.decode('utf-8').replace(systemPrompt, ''))
            for linerr in ssh_stderr.read().splitlines():
                print ('%s at %s on port %s' % (linerr.decode('utf-8').replace(systemPrompt, ''), \
                        self.servers['server'][i], self.servers['port'][i]))

            ssh[i].close()

    def do_lsn(self, options):
        "Get information about lss from every server"

        self.do_checkup(None)

        # List of servers from do_conn function
        ssh = sidefun.connect(self.servers)

        argv = options.split(' ')

        # If -f option is passed write to xboard.log and return
        if argv[0] == '-f':
            sidefun.filewrite('ls_release -a', ssh, self.servers)
            return

        # If an unknown option is passed display an error message and
        # return
        elif argv[0] != '-f' and argv[0] != '':
            print("Error: Unknown argument '%s' for command ls!" % argv[0])
            return

        sshLength = len(ssh)

        # Go through the list and execute the command for
        # every server

        print('\n')

        for i in range(0, sshLength):
            print(self.servers['server'][i], '\n')
            ssh_stdin, ssh_stdout, ssh_stderr = ssh[i].exec_command('ls -la')
            for line in ssh_stdout.read().splitlines():
                print(line.decode('utf-8').replace(systemPrompt, ''))
            for linerr in ssh_stderr.read().splitlines():
                if linerr:
                    print ('%s at %s on port %s' % (linerr.decode('utf-8').replace(systemPrompt, ''), \
                            self.servers['server'][i], self.servers['port'][i]))
            print('============================================')

            ssh[i].close()

    def do_export(self, inp):
        """Export all data to a csv file. Run checkup first!!!"""

        ssh = sidefun.connect(self.servers)
        sshLength = len(ssh)

        if os.path.isfile('./exported.csv'):
            with open('exported.csv', 'w+') as exportFile:
                exportFile.write("index,type,ip,state,fw_level,fw_version," + \
                        "release_date, uefi, uefi_release_date"  + "\n")


        for i in range(sshLength):

            csvline = []
            # index
            csvline.append(str(i+1))

            # type
            type_model = sidefun.sys(self.servers['server'][i], \
                    self.servers['user'][i], self.servers['password'][i], \
                    self.servers['port'][i])
            csvline.append(type_model)

            # server ip
            csvline.append(self.servers['server'][i])

            # power state
            power = sidefun.powerstatus(self.servers['server'][i], \
                    self.servers['user'][i], self.servers['password'][i], \
                    self.servers['port'][i])
            csvline.append(power.split()[1])

            # firmware info
            csvline.extend(sidefun.fw(self.servers['server'][i], \
                    self.servers['user'][i], self.servers['password'][i], \
                    self.servers['port'][i]))

            with open('exported.csv', 'a+') as exportFile:
                line = ','.join(csvline)
                exportFile.write(line + '\n')


    def do_log(self, inp):
        "Display log info"
        os.system('less xboard.log')

    def do_clrlog(self, inp):
        # TODO maybe delete after or before a given date
        "Delete log info"
        os.system('> xboard.log')

    def do_ls(self, inp):
        "List the initial servers from xboard.cfg"
        import loadcfg

        data = loadcfg.loadcfg()
        for i in data['server']:
            print(i)

    def do_lsu(self, inp):
        "List the servers"
        import loadcfg

        data = self.servers

        if not data['server']:
            print("There are no alive servers to track! Abort..")
            return

        for i in data['server']:
            print(i)

    def do_lso(self, inp):
        """List powered off servers.
        Options: -u power on the servers listed here"""
        data = self.off

        if not data['server']:
            print("There are no powered off servers to track! Abort..")
            return

        for i in data['server']:
            print(i)

        if '-u' == inp:
            print('\n')
            for i in range(len(self.off['server'])):
                sidefun.poweron(self.off['server'][i], \
                        self.off['user'][i], self.off['password'][i], \
                        self.off['port'][i])

    def do_lp(self, inp):
        "List the ports"
        import loadcfg

        data = self.servers
        for i in data['port']:
            print(i)


    def do_lu(self, inp):
        "List users"
        import loadcfg

        data = self.servers
        for i in data['user']:
            print(i)

    def do_exit(self, inp):
        print("\nExit..")
        return True

try:
    xBoard().preloop()
    xBoard().cmdloop()
except KeyboardInterrupt:
    xBoard().postloop()
    print("\nExit..")
    sys.exit(0)
