import datetime
import os
import paramiko
import loadcfg

def filewrite(func, ssh, servers):
    with open('xboard.log', 'a+') as log:

        # If the file is not empty place two lines between
        # every set of info
        if os.stat("xboard.log").st_size != 0:
            log.write("\n\n")

        sshLength = len(ssh)

        now = datetime.datetime.now()

        # Date and time info about log
        log.write('Informations about %s at %s\n' % (func, now.strftime("%Y-%m-%d %H:%M")))

        # Writing stdout of commands into file
        for i in range(0, sshLength):
            ssh_stdin, ssh_stdout, ssh_stderr = ssh[i].exec_command(func)
            for line in ssh_stdout.read().splitlines():
                log.write('%s\n' % line.decode('utf-8'))
            for linerr in ssh_stderr.read().splitlines():
                log.write('%s at %s on port %s\n' % (linerr.decode('utf-8'), \
                        servers['server'][i], servers['port'][i]))

def connect(servers):

    data = servers
    dataLength = len(data['server'])

    ssh = []

    for i in range(0, dataLength):
        # This line creates a new cell in the list with a ssh object
        ssh.append(paramiko.SSHClient())
        ssh[i].set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh[i].connect(data['server'][i], port = int(data['port'][i]), \
                username=data['user'][i], password=data['password'][i])

    return ssh

def powerstatus(server, user, password, port):
    connection = paramiko.SSHClient()
    connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connection.connect(server, int(port), user, password)
    ssh_stdin, ssh_stdout, ssh_stderr = connection.exec_command('power state')

    pwstatus = 'test'

    try:
        tmp = ssh_stdout.read().splitlines()
        pwstatus = tmp[0][2].decode('utf-8')
    except:
        print("exception powerstatus")

    connection.close()

    ##return stdout or stdout
    return pwstatus

def poweron(server, user, password, port):
    connection = paramiko.SSHClient()
    connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connection.connect(server, int(port), user, password)
    ssh_stdin, ssh_stdout, ssh_stderr = connection.exec_command('power on')

    try:
        ssh_stdout = ssh_stdout.read().splitlines()[0].decode('utf-8')
    except:
        print("exception poweron")

    connection.close()

    print(ssh_stdout)

    # Check if it was successful

def fw(server, user, password, port):

    # List which contains first and third line with the fields
    # 2 and 4
    fw_list = []

    connection = paramiko.SSHClient()
    connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connection.connect(server, int(port), user, password)
    ssh_stdin, ssh_stdout, ssh_stderr = connection.exec_command('vpd fw')

    try:
        tmp = ssh_stdout.read().splitlines()
        #bmc = ssh_stdout.read().splitlines()[3].decode('utf-8')
        bmc = tmp[2].decode('utf-8')
        #uefi = ssh_stdout.read().splitlines()[5].decode('utf-8')
        uefi = tmp[4].decode('utf-8')

        bmc = bmc.split()
        uefi = uefi.split()

        fw_list.append(bmc[0])
        fw_list.append(bmc[2])
        fw_list.append(bmc[4])
        fw_list.append(uefi[2])
        fw_list.append(uefi[4])

    except:
        print("exception vpd fw")

    connection.close()

    return fw_list

def sys(server, user, password, port):

    connection = paramiko.SSHClient()
    connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connection.connect(server, int(port), user, password)
    ssh_stdin, ssh_stdout, ssh_stderr = connection.exec_command('vpd sys')

    try:
        #type_model = ssh_stdout.read().splitlines()[2].decode('utf-8')
        tmp = ssh_stdout.read().splitlines()
        tmp1 = tmp[2].decode('utf-8')
        tmp2 = tmp1.split()
        type_model = tmp2[0]
    except:
        print("exception vpd sys")
        return "oops"

    connection.close()

    return type_model

