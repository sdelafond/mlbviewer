#!/usr/bin/env python

from MLBviewer import *
import os
import sys
import re
import curses
import curses.textpad
import select
import datetime
import subprocess
import time
import pickle
import copy


def padstr(s,num):
    if len(str(s)) < num:
        p = num - len(str(s))
        return ' '*p + s
    else:
        return s


myconfdir = os.path.join(os.environ['HOME'],AUTHDIR)
myconf =  os.path.join(myconfdir,AUTHFILE)
mydefaults = {'speed': DEFAULT_SPEED,
              'video_player': DEFAULT_V_PLAYER,
              'audio_player': DEFAULT_A_PLAYER,
              'audio_follow': [],
              'video_follow': [],
              'blackout': [],
              'favorite': [],
              'use_color': 0,
              'favorite_color': 'cyan',
              'bg_color': 'xterm',
              'show_player_command': 0,
              'debug': 0,
              'x_display': '',
              'top_plays_player': '',
              'time_offset': ''}

mycfg = MLBConfig(mydefaults)
mycfg.loads(myconf)

cfg = mycfg.data

# check to see if the start date is specified on command-line
if len(sys.argv) > 1:
    pattern = re.compile(r'(.*)=(.*)')
    parsed = re.match(pattern,sys.argv[1])
    if not parsed:
        print 'Error: Arguments should be specified as variable=value'
        sys.exit()
    split = parsed.groups()
    if split[0] not in ('startdate'):
        print 'Error: unknown variable argument: '+split[0]
        sys.exit()

    pattern = re.compile(r'startdate=([0-9]{1,2})(/)([0-9]{1,2})(/)([0-9]{2})')
    parsed = re.match(pattern,sys.argv[1])
    if not parsed:
        print 'Error: listing start date not in mm/dd/yy format.'
        sys.exit()
    split = parsed.groups()
    startmonth = int(split[0])
    startday  = int(split[2])
    startyear  = int('20' + split[4])
    startdate = (startyear, startmonth, startday)
else:
    now = datetime.datetime.now()
    dif = datetime.timedelta(1)
    if now.hour < 9:
        now = now - dif
    startdate = (now.year, now.month, now.day)

mysched = MiLBSchedule(ymd_tuple=startdate,time_shift=mycfg.get('time_offset'))

try:
    available = mysched.getListings(mycfg.get('speed'),mycfg.get('blackout'))
except (KeyError, MLBXmlError), detail:
    if cfg['debug']:
        raise Exception, detail
    available = []
    #raise 
    print "There was a parser problem with the listings page"
    sys.exit()

# This is more for documentation. Mlblistings.py is meant to produce more 
# machine readable output rather than user-friendly output like mlbviewer.py.
statusline = {
    "I" : "Status: In Progress",
    "W" : "Status: Not Yet Available",
    "F" : "Status: Final",
    "CG": "Status: Final (Condensed Game Available)",
    "P" : "Status: Not Yet Available",
    "S" : "Status: Suspended",
    "D" : "Status: Delayed",
    "IP": "Status: Pregame",
    "PO": "Status: Postponed",
    "GO": "Status: Game Over - stream not yet available",
    "NB": "Status: National Blackout",
    "LB": "Status: Local Blackout"}

print "MiLB.TV Listings for " +\
    str(mysched.month) + '/' +\
    str(mysched.day)   + '/' +\
    str(mysched.year)

for n in range(len(available)):
    # This is how you can recreate the mlbviewer output (e.g. user-friendly)
    # You would uncomment the print str(s) line and comment out the 
    # the print str(c) 
    # Or mix and match between the lines to produce the output you find
    # easiest for you (such as printing raw home and away teamcodes without 
    # translating them in the TEAMCODES dictionary, e.g.
    # "kc at tex"  instead of "Kansas City Royals at Texas Rangers"
    home = available[n][0]['home']
    away = available[n][0]['away']
    s = available[n][1].strftime('%l:%M %p') + ': ' +\
       ' '.join(TEAMCODES[away][1:]).strip() + ' at ' +\
       ' '.join(TEAMCODES[home][1:]).strip()
    #print str(s)
    c = padstr(available[n][5],2) + ": " +\
        available[n][1].strftime('%l:%M %p') + ': ' +\
        available[n][6] 
    try:
        c += ' C:' + padstr(str(available[n][2][0][2]),9)
    except (TypeError, IndexError):
        c += ' C:' + padstr('None',9)
    print str(c)

