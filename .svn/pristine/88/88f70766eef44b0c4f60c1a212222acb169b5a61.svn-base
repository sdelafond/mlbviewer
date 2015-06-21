#!/usr/bin/env python

from mlbProcess import MLBprocess
from mlbError import *
from mlbConstants import *
from mlbLog import MLBLog
from mlbConfig import MLBConfig
from mlbMediaStream import MediaStream

import re
import os

class MLBClassicsStream(MediaStream):

    def __init__(self,url,cfg):
        # skeleton init to take advantage of MediaStream's cmdStr formatting
        self.mediaUrl = url
        self.cfg = cfg
        self.streamtype='classics'
        self.stream = ('MLB.COM', '000', '123456', '00-0000-1970-01-01')


