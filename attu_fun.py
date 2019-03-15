from datetime import datetime
from pexpect import pxssh
import argparse
import os
import sys
import csv
from multiprocessing import Pool
import threading
import time

# Bug your friends and log their activity on attu!
# python attu_fun.py                    (logs all users on attu, uptimes, etc)
# python attu_fun.py -u user1 user2 user3  (writes defualt message to targets)
# python attu_fun.py -f ascii.txt userN (custom message)

# Alex DeMeo - alexd8
# Brian Bartels - bdb24
# Jake Sippy - jsippy

# private ssh key location
SSH_KEY='/Users/prestoncrowe/.ssh/id_rsa'
parser = argparse.ArgumentParser(description='Bug your friends and log their activity on attu!')
parser.add_argument('-u', nargs='+', help='list of target usernames')
parser.add_argument('-f', nargs='?', help='filename of text to send')
parser.add_argument('--evil', action="store_true", help='>:)')
args = parser.parse_args()

def main():
    all_users = []
    pool = Pool(7)
    pool.map(write_targets_on_attu, range(1,8))
    log_activity(all_users)

# Writes every logged in user on the given attu server who
# appears in argv target list
# Returns the result of finger on the given attu server as
# a list of users
def write_targets_on_attu(attu):
    result = []
    s = pxssh.pxssh()
    if not s.login ('attu%d.cs.washington.edu' % attu, 'pcrowe', ssh_key=SSH_KEY):
        print "[-] SSH session failed on login."
        print str(s)
    else:
        s.sendline('tty')
        s.prompt()

        tty = s.before
        tty = tty.split('\n')[1][5:]
        print('[+] SSH session succeeded on attu{} on tty {}'.format(attu, tty))
        s.sendline('finger')
        s.prompt()

        # Split on newlines, ditch the first two header lines
        lines = s.before.split('\n')[2:]

        # Convert all lines to tuples
        users = map(lambda u: finger_to_tuple(attu, u), lines)

        # Remove any instances of None from users (goddamn newlines...)
        result = filter(None, users)

        print(result[0][3])
        print(tty)
        result = filter(lambda x: x[3] != tty, result)
        print len(result)

        if (args.u):
            # Filter all users to only the ones we're interested in
            targets = filter(lambda x: x[1] in args.u, result)
        
            if (args.evil):
                spam(s,targets)

            # Send it
            for u in targets:
                print('\tSending message to {} on attu{}...'.format(u[1], attu))
                if (args.f):
                    f = open(args.f, 'r')
                    contents = f.read()
                    s.sendline('write {} {}'.format(u[1], contents[:100]))
                else:
                    s.sendline ('write {} {}'.format(u[1], u[3]))
                    s.sendline ('Hi {}! Your ip is {}. Have a nice day (:'
                                .format(u[2], u[4]))
                s.sendeof()

        if (args.evil == False):
            s.logout()
    return result

# Evil mode, spams users round robin for forever and ever
def spam(session, targets):
    while(True):
        for user in targets:
            time.sleep(1)
            print (user)
            session.sendline ('write {} {}'.format(user[1], user[3]))
            session.sendline ('Hi {}! Your ip is {}. Have a nice day (:'
                        .format(user[2], user[4]))

# Logs output of finger to csv
def log_activity(users):
    filename = datetime.now().strftime('%Y-%m-%d-%H:%M:%S') + '.csv'
    with open('logs/{}'.format(datetime.now()), mode='w') as output:
        writer = csv.writer(output, delimiter=',', quotechar='"')
        writer.writerow(['attu', 'username', 'name', 'tty', 'ip'])
        for user in users:
            writer.writerow(user)

# Accepts a single line from the output of finger and returns
# a tuple containing the relevant user data
def finger_to_tuple(attu, line):
    tokens = line.split()
    if (len(tokens) < 4):
        return None

    name = tokens[1] + ' ' + tokens[2]
    username = tokens[0]
    tty = tokens[3]
    host_ip = tokens[len(tokens) - 1].replace("(", "").replace(")","")
    return (attu, username, name, tty, host_ip)

if __name__ == "__main__":
    main()
