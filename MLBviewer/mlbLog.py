#!/usr/bin/env python

# mlbviewer is free software; you can redistribute it and/or modify
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, Version 2.
#
# mlbviewer is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# For a copy of the GNU General Public License, write to the Free
# Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# 02111-1307 USA

import urllib
import urllib2
import re
import time
from datetime import datetime
import cookielib

import os
import subprocess
import select
from copy import deepcopy
import sys

from mlbProcess import MLBprocess
from mlbConstants import *

class MLBLog:

    def __init__(self,logfile):
        self.logfile = logfile
        self.log = None

    def open(self):
        self.log = open(self.logfile,"a")
    
    def close(self):
        if self.log is not None:
            self.log.close()
        self.log = None

    def flush(self):
        pass
    
    def write(self,logmsg):
        ts=datetime.now().strftime('%m/%d %H:%M | ')
        if self.log is None:
            self.open()
        self.log.write(ts + logmsg + '\n')
        self.close()

