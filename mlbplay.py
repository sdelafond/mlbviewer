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

def check_bool(userinput):
    if userinput in ('0', '1', 'True', 'False'):
        return eval(userinput)

# This section prepares a dict of default settings and then loads 
# the configuration file.  Any setting defined in the configuration file 
# overwrites the defaults defined here.
#
# Note: AUTHDIR, AUTHFILE, etc are defined in MLBviewer/mlbtv.py
myconfdir = os.path.join(os.environ['HOME'],AUTHDIR)
myconf =  os.path.join(myconfdir,AUTHFILE)
mydefaults = {'speed': DEFAULT_SPEED,
              'video_player': DEFAULT_V_PLAYER,
              'audio_player': DEFAULT_A_PLAYER,
              'audio_follow': [],
              'alt_audio_follow': [],
              'video_follow': [],
              'blackout': [],
              'favorite': [],
              'use_color': 0,
              'adaptive_stream': 1,
              'favorite_color': 'cyan',
              'bg_color': 'xterm',
              'show_player_command': 0,
              'debug': 0,
              'x_display': '',
              'top_plays_player': '',
              'use_librtmp': 0,
              'use_nexdef': 0,
              'condensed' : 0,
              'nexdef_url': 0,
              'adaptive_stream': 1,
              'zdebug' : 0,
              'time_offset': ''}

mycfg = MLBConfig(mydefaults)
mycfg.loads(myconf)

# initialize some defaults
startdate = None

teamcodes_help = "\n" +\
"Valid teamcodes are:" + "\n" +\
"\n" +\
"     'ana', 'ari', 'atl', 'bal', 'bos', 'chc', 'cin', 'cle', 'col',\n" +\
"     'cws', 'det', 'mia', 'hou', 'kc', 'la', 'mil', 'min', 'nym',\n" +\
"     'nyy', 'oak', 'phi', 'pit', 'sd', 'sea', 'sf', 'stl', 'tb',\n" +\
"     'tex', 'tor', 'was'\n" +\
"\n"

if len(sys.argv) == 1:
    print "%s <key>=<value>" % sys.argv[0]
    print "examples:"
    print "%s v=ana   // plays the video stream for LA Angels" % sys.argv[0]
    print "%s a=nyy   // plays the audio stream for NY Yankees" % sys.argv[0]
    print ""
    print "See MLBPLAY-HELP for more options."
    print teamcodes_help
    sys.exit()

# All options are name=value, loop through them all and take appropriate action
if len(sys.argv) > 1:
    for n in range(len(sys.argv)):
        if n == 0:
            continue
        # first make sure the argument is of name=value format
        pattern = re.compile(r'(.*)=(.*)')
        parsed = re.match(pattern,sys.argv[n])
        if not parsed:
            print 'Error: Arguments should be specified as variable=value'
            print "can't parse : " + sys.argv[n]
            sys.exit()
        split = parsed.groups()
        # Event-id: e=<event-id>, can be found from mlblistings or z=1
        if split[0] in ( 'event_id' , 'e' ):
            mycfg.set('event_id', split[1])

        # Condensed game:  c=<teamcode> 
        elif split[0] in ( 'condensed', 'c'):
            streamtype='condensed'
            mycfg.set('condensed', True)
            teamcode = split[1]
            if mycfg.get('top_plays_player'):
                player = mycfg.get('top_plays_player')
            else:
                player = mycfg.get('video_player')
        # Audio: a=<teamcode>
        elif split[0] in ( 'audio', 'a' ):
            streamtype = 'audio'
            teamcode = split[1]
            player = mycfg.get('audio_player')
        # Video: v=<teamcode>
        elif split[0] in ( 'video', 'v' ):
            streamtype = 'video'
            teamcode = split[1]
            player = mycfg.get('video_player')
        # Speed: p=<speed> (Default: 1200)
        elif split[0] in ( 'speed', 'p' ):
            mycfg.set('speed', split[1])
        # Nexdef URL: nu=1
        elif split[0] in ( 'nexdefurl', 'nu' ):
            parsed = check_bool(split[1])
            if parsed != None:
                mycfg.set('nexdef_url', parsed)
        # Debug: d=1
        elif split[0] in ( 'debug', 'd' ):
            parsed = check_bool(split[1])
            if parsed != None:
                mycfg.set('debug', parsed)
        elif split[0] in ( 'inning', 'i' ):
            mycfg.set('start_inning', split[1]) 
        # Listing debug: z=1
        elif split[0] in ( 'zdebug', 'z' ):
            parsed = check_bool(split[1])
            if parsed != None:
                mycfg.set('zdebug', parsed)
        elif split[0] in ('keydebug', 'k' ):
            parsed = check_bool(split[1])
            if parsed != None:
                mycfg.set('keydebug', parsed)
        # Nexdef: n=1
        elif split[0] in ( 'nexdef', 'n' ):
            parsed = check_bool(split[1])
            if parsed != None:
                mycfg.set('use_nexdef', parsed)
        # Startdate: j=mm/dd/yy
        elif split[0] in ( 'startdate', 'j'):
            try:
                sys.argv[n] = sys.argv[n].replace('j=', 'startdate=')
            except:
                 raise
            pattern = re.compile(r'startdate=([0-9]{1,2})(/)([0-9]{1,2})(/)([0-9]{2})')
            parsed = re.match(pattern,sys.argv[n])
            if not parsed:
                print 'Error: listing start date not in mm/dd/yy format.'
                sys.exit()
            split = parsed.groups()
            startmonth = int(split[0])
            startday  = int(split[2])
            startyear  = int('20' + split[4])
            # not sure why jesse went with yy instead of yyyy but let's 
            # throw an error for 4 digit years for the heck of it.
            if startyear == 2020:
                print 'Error: listing start date not in mm/dd/yy format.'
                sys.exit()
            startdate = (startyear, startmonth, startday)
        else:
            print 'Error: unknown variable argument: '+split[0]
            sys.exit()

if startdate is None:
    now = datetime.datetime.now()
    dif = datetime.timedelta(1)
    if now.hour < 9:
        now = now - dif
    startdate = (now.year, now.month, now.day)

# First create a schedule object
mysched = MLBSchedule(ymd_tuple=startdate,time_shift=mycfg.get('time_offset'))

# Now retrieve the listings for that day
try:
    available = mysched.getListings(mycfg.get('speed'), mycfg.get('blackout'))
except (KeyError, MLBXmlError), detail:
    if cfg.get('debug'):
        raise Exception, detail
    available = []
    #raise 
    print "There was a parser problem with the listings page"
    sys.exit()

# Determine media tuple using teamcode e.g. if teamcode is in home or away, use
# that media tuple.  A media tuple has the format: 
#     ( call_letters, code, content-id, event-id )
# The code is a numerical value that maps to a teamcode.  It is used
# to identify a media stream as belonging to one team or the other.  A code
# of zero is used for national broadcasts or a broadcast that isn't owned by
# one team or the other.
if teamcode is not None:
    if teamcode not in TEAMCODES.keys():
        print 'Invalid teamcode: ' + teamcode
        print teamcodes_help
        sys.exit()
    media = []
    for n in range(len(available)):
        home = available[n][0]['home']
        away = available[n][0]['away']
        if teamcode in ( home, away ):
            listing = available[n]
            gameid = available[n][6].replace('/','-')
            if streamtype ==  'video':
                media.append(available[n][2])
            elif streamtype == 'condensed':
                media.append(available[n][2])
                condensed_media = available[n][4]
            else:
                media.append(available[n][3])
            eventId = available[n][6]

# media assigned above will be a list of both home and away media tuples
# This next section determines which media tuple to use (home or away)
# and assign it to a stream tuple.

# Added to support requesting specific games of a double-header
cli_event_id = mycfg.get('event_id')

if len(media) > 0:
    stream = None
    for m in media:
        for n in range(len(m)):
            ( call_letters,
              code,
              content_id,
              event_id ) = m[n]
            if cli_event_id is not None:
                if cli_event_id != event_id:
                    continue
            if code == TEAMCODES[teamcode][0] or code == '0':
                if streamtype == 'condensed':
                    stream = condensed_media[0]
                else:
                    stream = m[n]
                break
else:
    print 'Could not find media for teamcode: ' + teamcode
    sys.exit()

# Similar behavior to the 'z' key in mlbviewer
if mycfg.get('zdebug'):
    print 'media = ' + repr(media)
    print 'prefer = ' + repr(stream)
    sys.exit()

# Before creating GameStream object, get session data from login
session = MLBSession(user=mycfg.get('user'),passwd=mycfg.get('pass'),
                     debug=mycfg.get('debug'))
if mycfg.get('keydebug'):
    sessionkey = session.readSessionKey()
    print "readSessionKey: " + sessionkey
session.getSessionData()
# copy all the cookie data to pass to GameStream
mycfg.set('cookies', {})
mycfg.set('cookies', session.cookies)
mycfg.set('cookie_jar', session.cookie_jar)

# Jump to innings returns a start_time other than the default behavior
if mycfg.get('start_inning') is not None:
    streamtype = 'video'
    jump_pat = re.compile(r'(B|T|E|D)(\d+)?')
    match = re.search(jump_pat, mycfg.get('start_inning').upper())
    innings = mysched.parseInningsXml(stream[3], mycfg)
    if match is not None:
        if match.groups()[0] == 'D':
            print "retrieving innings index for %s" % stream[3]
            print repr(innings)
            sys.exit()
        elif match.groups()[0] not in ('T', 'B', 'E' ):
            print "You have entered an invalid half inning."
            sys.exit()
        elif match.groups()[1] is None:
            print "You have entered an invalid half inning."
            sys.exit()
        elif match.groups()[0] == 'T':
            half = 'away'
            inning = int(match.groups()[1])
        elif match.groups()[0] == 'B':
            half = 'home'
            inning = int(match.groups()[1])
        elif match.groups()[0] == 'E':
            half = 'away'
            inning = 10
    try:
        start_time = innings[inning][half]
    except:
        print "You have entered an invalid or unavailable half inning."
        sys.exit()
        

# Once the correct media tuple has been assigned to stream, create the 
# MediaStream object for the correct type of media
if stream is not None:
    if streamtype == 'audio':
        m = MediaStream(stream, session=session,
                        cfg=mycfg,
                        streamtype='audio')
    elif streamtype in ( 'video', 'condensed'):
        try:
            start_time
        except NameError:
            start_time = 0
        if mycfg.get('use_nexdef'):
            if mycfg.get('start_inning') is None:
                start_time = mysched.getStartOfGame(listing, mycfg)
        m = MediaStream(stream, session=session,
                        streamtype=streamtype,
                        cfg=mycfg,start_time=start_time)
    else:
        print 'Unknown streamtype: ' + repr(streamtype)
        sys.exit()
else:
    print 'Stream could not be found.'
    print 'Media listing debug information:'
    print 'media = ' + repr(media)
    print 'prefer = ' + repr(stream)
    sys.exit()

# Post-rewrite, the url beast has been replaced with locateMedia() which 
# returns a raw url.  
try:
    mediaUrl = m.locateMedia()
except:
    if mycfg.get('debug'):
        raise
    else:
        print 'An error occurred locating the media URL:'
        print m.error_str
        #sys.exit()

if mycfg.get('keydebug'):
    sessionkey = session.readSessionKey()
    print "Session-key from media request: " + sessionkey

if mycfg.get('nexdef_url'):
    print mediaUrl
    sys.exit()

if mycfg.get('debug'):
    print 'Media URL received: '
    print mediaUrl
    #sys.exit()

# prepareMediaStreamer turns a raw url into either an mlbhls command or an 
# rtmpdump command that pipes to stdout
mediaUrl = m.prepareMediaStreamer(mediaUrl)

# preparePlayerCmd is the second half of the pipe using *_player to play
# media from stdin
if cli_event_id is not None:
    eventId = cli_event_id
cmdStr   = m.preparePlayerCmd(mediaUrl,eventId,streamtype)

if mycfg.get('show_player_command') or mycfg.get('debug'):
    print cmdStr
    if mycfg.get('debug'):
        sys.exit()

try:
    
    #playprocess = subprocess.Popen(cmdStr,shell=True)
    #playprocess.wait()
    play = MLBprocess(cmdStr)
    play.open()
    play.wait()
    play.close()
except KeyboardInterrupt:
    play.close()
    sys.exit()
except:
    raise

