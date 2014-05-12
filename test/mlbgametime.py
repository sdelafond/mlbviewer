#!/usr/bin/env python

import sys

try:
    from MLBviewer import *
except:
    print "Please copy this script to mlbviewer directory and run again."
    sys.exit()

from datetime import datetime, timedelta

edt=datetime.now()

print "[1] START WITH A TYPICAL GAME TIME (10:05 PM EDT.)"
edt=edt.replace(hour=22, minute=5)
print "%s" % edt.strftime('%I:%M %p')

print ""
print "[2] USING MLBGameTime, PRINT THE UTC OFFSET FOR EDT"
print "(4:00:00 during baseball season. 5:00:00 during offseason.)"
gt=MLBGameTime(edt)
print "%s" % gt.utcoffset()

print ""
print "[3] USING MLBGameTime, LOCALIZE THIS TIME"
local=gt.localize()
print "%s" % local.strftime('%I:%M %p')

print ""
print "Is that a correct localization?"
print ""
print "* If [2] is not 4:00:00 during baseball season or 5:00:00 in offseason,"
print "the US/Eastern to UTC conversion is wrong."
print ""

print "* If [3] does not produce a correct localization of a 10:05 PM EDT game,"
print "python's built-in datetime.localtime() is wrong.  You will need a time_offset="
print "option in your config.  The format is +/-hours:minutes from EDT."
print "The + or - sign is required. For example, UTC+1 should be time_offset=+5:00."
