#!/usr/bin/env python

import datetime
from datetime import tzinfo
import time
import re
 
# In the US, since 2007, DST starts at 2am (standard time) on the second
# Sunday in March, which is the first Sunday on or after Mar 8.
DSTSTART = datetime.datetime(1, 3, 8, 2)
# and ends at 2am (DST time; 1am standard time) on the first Sunday of Nov.
DSTEND = datetime.datetime(1, 11, 1, 1)


def first_sunday_on_or_after(dt):
    days_to_go = 6 - dt.weekday()
    if days_to_go:
        dt += datetime.timedelta(days_to_go)
    return dt

class MLBGameTime:

    def __init__(self,listtime,shift=None):
        self.eastern = listtime
        self.shift = shift

    def dst(self):
        dststart, dstend = DSTSTART, DSTEND
        
        dston = first_sunday_on_or_after(dststart.replace(year=self.eastern.year))
        dstoff = first_sunday_on_or_after(dstend.replace(year=self.eastern.year))
        if dston <= self.eastern.replace(tzinfo=None) < dstoff:
            return datetime.timedelta(hours=1)
        else:
            return datetime.timedelta(0)

    def utcoffset(self):
        return datetime.timedelta(hours=5) - self.dst()

    def localize(self):
        if self.shift is not None and self.shift != '':
            return self.override(offset=self.shift)
        utctime = self.eastern + self.utcoffset()
        now = time.localtime()
        localzone = (time.timezone,time.altzone)[now.tm_isdst]
        localoffset = datetime.timedelta(0,localzone)
        localtime = utctime - localoffset
        return localtime


    def customoffset(self,time_shift,reverse=False):
        try:
            plus_minus=re.search('[+-]',time_shift).group()
            (hrs,min)=time_shift[1:].split(':')
            offset=datetime.timedelta(hours=int(plus_minus+hrs),minutes=int(min))
            offset=(offset,offset*-1)[reverse]
        except:
            raise
            offset=datetime.timedelta(0,0)
        return offset

    def override(self,offset,reverse=False):
        if offset is not None and offset != '':
            localoffset = self.customoffset(time_shift=offset,reverse=reverse)
            localtime = self.eastern + localoffset
            return localtime
        else:
             return self.eastern
        

