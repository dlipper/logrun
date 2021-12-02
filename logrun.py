# logrun# -*- coding: utf-8 -*-
"""
NAME: LogRun
VERSION: 2.0.0
COMMIT: EVTX file support
AUTHOR: Dmytro Petrashchuk
EMAIL: dpgbox@gmail.com

Prerequisites for script
    1. Install Python 3.7 or later
    2. Install additional packages with "pip install -r requirements.txt"
    3. Use command line parameters
    4. Try -h option to get detailed help on usage
    5. Look into the code to get additional insights
    6. Don't stop yourself to use this script as you want and suggest your changes
"""


import argparse
import requests
from time import sleep
import socket
from datetime import datetime
#from Evtx.Evtx import Evtx
import xmltodict

# Ignore SSL-warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

"""Place the program description here """
DESCRIPTION = ''' Script to send syslog from file (plain or evtx) to syslog server (based on IBM QRadar script logrun.pl). '''

__all__ = ['logrun']

"""Base constants and paths """
FACILITY = {
    'kern': 0, 'user': 1, 'mail': 2, 'daemon': 3,
    'auth': 4, 'syslog': 5, 'lpr': 6, 'news': 7,
    'uucp': 8, 'cron': 9, 'authpriv': 10, 'ftp': 11,
    'local0': 16, 'local1': 17, 'local2': 18, 'local3': 19,
    'local4': 20, 'local5': 21, 'local6': 22, 'local7': 23,
}

LEVEL = {
    'emerg': 0, 'alert': 1, 'crit': 2, 'err': 3,
    'warning': 4, 'notice': 5, 'info': 6, 'debug': 7
}

"""The list of command-line arguments """
ARGUMENTS = {
    'eps':
    {
        'help': 'messages per second',
        'dest': 'eps',
        'type': 'mandatory'
    },
    'dest':
    {
        'help': 'destination syslog host (default 127.0.0.1)',
        'dest': 'dest',
        'type': 'optional'
    },
    'port':
    {
        'help': 'destination port (default 514)',
        'dest': 'port',
        'type': 'optional'
    },
    'filename':
    {
        'help': 'filename to read (default readme.syslog)',
        'dest': 'filename',
        'type': 'optional'
    },
    'object':
    {
        'help': 'use OBJECT for object name in syslog header',
        'dest': 'object',
        'type': 'optional'
    },
    'sourceip':
    {
        'help': 'use this IP as spoofed sender (default is NOT to send IP header)',
        'dest': 'srcip',
        'type': 'optional'
    },
    'v':
    {
        'help': 'verbose, display lines read in from file',
        'dest': 'verbose',
        'type': 'flag'
    },
    't':
    {
        'help': 'use TCP instead of UDP for sending syslogs',
        'dest': 'tcp',
        'type': 'flag'
    },
    'b':
    {
        'help': 'burst the same message for 20%% of the delay time',
        'dest': 'burst',
        'type': 'flag'
    },
    'l':
    {
        'help': 'loop indefinately',
        'dest': 'loop',
        'type': 'flag'
    },
    'p':
    {
        'help': 'propagate the Source IP from object name in every line - ^([^:]+): - starts from line begining and is closed by :',
        'dest': 'propagate',
        'type': 'flag'
    }
}


class LogRun:
    """Main module functional object wrapper.

    Reads file and send to syslog server
    Args:
        args(dict): all the arguments from command line passed as dict.
                    Correspond to list of attributes
    Attributes:
        dest(string): syslog server to send messages to
        port(int): syslog server port
        eps(int): Events per second rate
    """

    def __init__(self, args):
        # Init properties
        self.dest = args['dest'] if args.get('dest') else '127.0.0.1'
        self.port = int(args['port']) if args.get('port') else 514
        self.eps = int(args['eps'])
        self.filename = args['filename'] if args.get(
            'filename') else 'readme.syslog'
        self.object = args['object'] if args.get('object') else None
        self.srcip = args['srcip'] if args.get('srcip') else None
        self.verbose = args.get('verbose') if args.get('verbose') else False
        self.protocol = 'tcp' if args.get('tcp') == True else 'udp'
        self.burst = args.get('burst') if args.get('burst') else False
        self.loop = args.get('loop') if args.get('loop') else False
        self.propagate = args.get('propagate') if args.get(
            'propagate') else False
        if self.filename.split('.')[-1] == 'evtx':
            self.evtx = True

    def run(self):
        """ Run the main cycle of reading file and sending to syslog
        Args:
            none
        Result:
            none
        """
        # Calculate the delay
        delay = 1/self.eps
        resolution = 0.2
        burst = round(self.eps * resolution)

        if self.burst:
            print('Sending $burst messages every {} ms'.format(delay*1000))

        # Initialize the loop
        loop = True
        while loop:
            """if self.evtx:

                # Read the evtx
                try:
                    with Evtx(self.filename) as log:
                        for line in log.records():
                            self.process_line(self.parse_xml(line.xml()), delay, burst)
                except IOError:
                    print('Unable to parse evtx file:'+self.filename)
                    exit(1)
            else:
            """    # Read the plain file
            try:
                with open(self.filename, 'r', encoding='utf-8') as log:
                    for line in log:
                        self.process_line(line, delay, burst)
            except IOError:
                print('Unable to open file:'+self.filename)
                exit(1)
            loop = self.loop

    def parse_xml(self, xml):
        """ Parse XML formatted Windows event into string
        Args:
            xml(string): XML text to parse
        Returns:
            (string): string to send through syslog
        """
        print(xml)
        eventd = xmltodict.parse(xml)
        print(eventd)
        events = ''
        for element in eventd['Event']:
            if element[0] == '@':
                events = ' '.join([events,'{}="{}"'.format(
                    element[1::], eventd['Event'][element])])
            else:
                for subelement in eventd['Event'][element]:
                    print('---------------')
                    print(subelement)
        return events

    def process_line(self, line, delay, burst):
        """Print the line."""
        if self.verbose:
            print(line)
        # Propagate
        if self.propagate:
            splitted = line.split(': ')
            line = ': '.join(splitted[1::])
            self.srcip = splitted[0]
        # Burst
        if self.burst:
            for i in range(1, burst):
                self.syslog(message=line, protocol=self.protocol,
                            dest=self.dest, port=self.port, object=self.object, src=self.srcip)
        # or just send syslog
        else:
            self.syslog(message=line, protocol=self.protocol,
                        dest=self.dest, port=self.port, object=self.object, src=self.srcip)
        if (delay > 0):
            if self.verbose:
                print('waiting for {} ms ...'.format(
                    delay * 1000))
            sleep(delay)

    def syslog(self, message='', facility=FACILITY['local6'], loglevel=LEVEL['info'], protocol='udp', port=514, dest='127.0.0.1', object=None, src=None):
        """ Send message to syslog
        Args:
            message(string): the message to send
            facility(int): syslog facility (default LOCAL6)
            loglevel(int): syslog level (default INFO)
            protocol(string): tcp or udp
            dest(string): IP address of syslog server
            object(string): Object name to place into syslog header
            src(string): IP address of syslog source
        Result:
            (bool) True if successfull
        """

        if (not src) and object:
            src = '127.0.0.1'
        if (not object) and src:
            object = 'logrun.py'
        object_string = object+'[73649]: ' if object else ''
        header = '<{:d}>{} {} {}'.format(loglevel + facility*8, datetime.now(
        ).strftime('%b %d %H:%M:%S'), src, object_string) if src else ''
        data = '%s%s' % (header, message)
        if self.verbose:
            print(data)
        if protocol == 'udp':
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(data.encode(), (dest, port))
            sock.close()
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((dest, port))
            sock.send(data.encode())
            sock.close()

# main function entry point


def main():
    """Parse the comand line arguments."""
    parser = argparse.ArgumentParser(
        description=DESCRIPTION)
    for arg in ARGUMENTS.keys():
        curarg = ARGUMENTS[arg]
        if curarg['type'] == 'mandatory':
            parser.add_argument(
                arg, help=curarg['help'])
        elif curarg['type'] == 'optional':
            parser.add_argument(
                '--'+arg, dest=curarg['dest'], help=curarg['help'])
        elif curarg['type'] == 'flag':
            parser.add_argument(
                '-'+arg, dest=curarg['dest'], action='store_true', help=curarg['help'])
    args = parser.parse_args()
    lr = LogRun(vars(args))
    print('generating {} messages per second to {}:{}'.format(
        lr.eps, lr.dest, lr.port))
    lr.run()


if __name__ == '__main__':
    main()
