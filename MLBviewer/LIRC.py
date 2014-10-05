#!/usr/bin/env python

# The following code is adapted from appleremote.py by Ben Firschman
# (c) 2008 (GPL v2). Baseball fans thank you, Ben.

import socket
import re
import logging
import time
from mlbConstants import LOGFILE

class LircConnection:
    """A connection to LIRC"""
    def __init__(self, dev="/dev/lircd", poll=0.01, program="mlbviewer", conffile = ".lircrc"):
        self.dev = dev
        self.poll = poll
        self.program = program
        self.conffile = conffile
        self.config = []
        self.conn = None
        self.connected = False
        self.retries = 3
        logging.basicConfig(filename=LOGFILE)
        #self.connect()
    
    def connect(self):
        """Connect to LIRC"""
        if self.connected:
            self.conn.close()
            self.connected = False
        try:
            self.conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.conn.connect(self.dev)
            self.conn.settimeout(self.poll)
            self.connected = True
        except socket.error, e:
            logging.warning("Could not connect to LIRC, retrying: %s" % e)
            time.sleep(0.5)
            if self.retries > 0:
                self.retries -= 1
                return self.connect()
            else:
                return None

    def getconfig(self):
        fp = open(self.conffile)
        out = []
        dct = {}
        for line in fp:
            if line.startswith('#'):
                pass
            elif re.match(r'^\s*$',line):
                pass
            elif line.strip().lower() == 'begin':
                READ = True
            elif line.strip().lower() == 'end':
                if dct['prog'] == self.program:
                    out.append(dct)
                READ = False
                dct = {}
            else:
                if READ:
                    key, val = line.split('=')
                    key = key.strip()
                    val = val.strip()
                    dct[key] = val

        self.config = out
        
    
    def next_code(self):
        """Gets next command from LIRC"""
        try:
            buf = self.conn.recv(1024)
            if buf:
                try:
                    # I'm sure this is grossly inefficient. If anyone
                    # wants to rewrite how it gets the key strokes,
                    # please please please do so.
                    cmd = [elem for elem in self.config if \
                               elem['button'].lower() == buf.split()[2].lower()\
                               and  \
                               elem['remote'].lower() == buf.split()[3].lower()][0]['config']
                    return cmd
                except:
                    return None
            else:
                self.connect()
                return self.next_code()
        except socket.timeout:
            return None
        except socket.error, e:
            logging.warning("Error reading from LIRC, reconnecting: %s" % e)
            self.connect()
            return self.next_code()
