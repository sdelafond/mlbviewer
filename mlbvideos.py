#!/usr/bin/env python

import curses
import curses.textpad
import datetime
import re
import select
import errno
import signal
import sys
import time
from MLBviewer import *

SPEEDTOGGLE = {
    "1200" : "[1200K]",
    "1800" : "[1800K]"}

# used for ignoring sigwinch signal
def donothing(sig, frame):
    pass

def doinstall(config,dct,dir=None):
    print "Creating configuration files"
    if dir:
        try:
            os.mkdir(dir)
        except:
            print 'Could not create directory: ' + dir + '\n'
            print 'See README for configuration instructions\n'
            sys.exit()
    # now write the config file
    try:
        fp = open(config,'w')
    except:
        print 'Could not write config file: ' + config
        print 'Please check directory permissions.'
        sys.exit()
    fp.write('# See README for explanation of these settings.\n')
    fp.write('# user and pass are required except for Top Plays\n')
    fp.write('user=\n')
    fp.write('pass=\n\n')
    for k in dct.keys():
        if type(dct[k]) == type(list()):
            if len(dct[k]) > 0:
                for item in dct[k]:
                    fp.write(k + '=' + str(dct[k]) + '\n')
                fp.write('\n')
            else:
                fp.write(k + '=' + '\n\n')
        else:
            fp.write(k + '=' + str(dct[k]) + '\n\n')
    fp.close()
    print
    print 'Configuration complete!  You are now ready to use mlbviewer.'
    print
    print 'Configuration file written to: '
    print
    print config
    print
    print 'Please review the settings.  You will need to set user and pass.'
    sys.exit()

def mainloop(myscr,mycfg,mykeys):

    # some initialization
    log = open(LOGFILE, "a")
    DISABLED_FEATURES = []
    # add in a keybinding for listings that makes sense, e.g. Menu
    mykeys.set('LISTINGS','m')
    CFG_SPEED = int(mycfg.get('speed'))
    if CFG_SPEED >= 1800:
        mycfg.set('speed',1800)
    else:
        mycfg.set('speed',1200)

    # not sure if we need this for remote displays but couldn't hurt
    if mycfg.get('x_display'):
        os.environ['DISPLAY'] = mycfg.get('x_display')

    try:
        curses.curs_set(0)
    except curses.error:
        pass

    # initialize the color settings
    if hasattr(curses, 'use_default_colors'):
        try:
            curses.use_default_colors()
            if mycfg.get('use_color'):
                try:
                    if mycfg.get('fg_color'):
                        mycfg.set('favorite_color', mycfg.get('fg_color'))
                    curses.init_pair(1, COLORS[mycfg.get('favorite_color')],
                                        COLORS[mycfg.get('bg_color')])
                except KeyError:
                    mycfg.set('use_color', False)
                    curses.init_pair(1, -1, -1)
        except curses.error:
            pass

    # initialize the input
    inputlst = [sys.stdin]


    # Default key : fastCast 
    # TODO: Fix this to use a config file param later
    DEFAULT_MLBTAX_KEY = 'wrapUp'

    mlbDailyMenu = MLBDailyMenuWin(myscr,mycfg)
    mlbDaily = MLBDailyVideos(mycfg)
    mlbDailyWin = MLBDailyVideoWin(myscr,mycfg,DEFAULT_MLBTAX_KEY,[])
    optwin = MLBOptWin(myscr,mycfg)
    mlbDailyWin.Splash()
    time.sleep(1)
    mywin = mlbDailyMenu

    mywin.titleRefresh()

    while True:
        myscr.clear()
        mywin.Refresh()
        mywin.titleRefresh()
        mywin.statusRefresh()

        # And now we do input.
        try:
            inputs, outputs, excepts = select.select(inputlst, [], [])
        except select.error, e:
            if e[0] != errno.EINTR:
                raise
            else:
                signal.signal(signal.SIGWINCH, signal.SIG_IGN)
                wiggle_timer = float(mycfg.get('wiggle_timer'))
                time.sleep(wiggle_timer)
                ( y , x ) = mywin.getsize()
                signal.signal(signal.SIGWINCH, donothing)
                curses.resizeterm(y, x)
                mywin.resize()
                continue


        if sys.stdin in inputs:
            c = myscr.getch()

        # NAVIGATION
        if c in mykeys.get('UP'):
            mywin.Up()
            continue

        if c in mykeys.get('DOWN'):
            mywin.Down()
            continue

        # TOGGLES
        if c in mykeys.get('SPEED'):
            speeds = map(int, SPEEDTOGGLE.keys())
            speeds.sort()
            newspeed = (speeds.index(int(mycfg.get('speed')))+1) % len(speeds)
            mycfg.set('speed', str(speeds[newspeed]))

        if c in mykeys.get('DEBUG'):
            if mycfg.get('debug'):
                mycfg.set('debug', False)
            else:
                mycfg.set('debug', True)

        # SCREENS
        if c in mykeys.get('LISTINGS') or c in mykeys.get('REFRESH'):
            mywin = mlbDailyMenu
            mywin.PgUp()
            
        if c in mykeys.get('OPTIONS'):
            optwin = MLBOptWin(myscr,mycfg)
            mywin = optwin

        if c in mykeys.get('MEDIA_DEBUG'):
            if mywin in ( optwin, ):
                continue
            myscr.clear()
            mywin.titlewin.clear()
            mywin.titlewin.addstr(0,0,'LISTING DEBUG')
            mywin.titlewin.hline(1, 0, curses.ACS_HLINE, curses.COLS-1)
            myscr.addstr(3,0,repr(mywin.records[mywin.current_cursor]))
            myscr.refresh()
            mywin.titlewin.refresh()
            mywin.statusWrite('Press a key to continue...',wait=-1)

        if c in mykeys.get('VIDEO') or c in ( 'Enter', 10 ):
            if mywin in ( optwin, ):
                continue
            if mywin == mlbDailyMenu:
                mywin.statusWrite('Refreshing listings...')
                vidkey = mywin.records[mywin.current_cursor]
                available = mlbDaily.getXmlList(vidkey)
                mywin = mlbDailyWin
                mywin.key = vidkey
                mywin.data = available
                mywin.records = available[0:curses.LINES-4]
                mywin.current_cursor = 0
                mywin.record_cursor = 0
                continue
                
            # Video selection and playback starts here
            mediaUrl = mlbDaily.getXmlItemUrl(mywin.records[mywin.current_cursor])[0]
            mediaStream = MLBDailyStream(mediaUrl,mycfg)
            cmdStr = mediaStream.preparePlayerCmd(mediaUrl,'MLBVIDEO','highlight')
            if mycfg.get('show_player_command'):
                myscr.clear()
                myscr.addstr(0,0,cmdStr)
                myscr.refresh()
                time.sleep(1)

            if mycfg.get('debug'):
                myscr.clear()
                chars=(curses.COLS-2) * (curses.LINES-1)
                myscr.addstr(0,0,cmdStr[:chars])
                myscr.refresh()
                mywin.statusWrite('DEBUG enabled: Displaying URL only.  Press any key to continue',wait=-1)
                continue

            play = MLBprocess(cmdStr)
            play.open()
            play.waitInteractive(myscr)

        if c in mykeys.get('QUIT'):
            curses.nocbreak()
            myscr.keypad(0)
            curses.echo()
            curses.endwin()
            break

if __name__ == "__main__":
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
                  'curses_debug': 0,
                  'wiggle_timer': 0.5,
                  'x_display': '',
                  'top_plays_player': '',
                  'time_offset': '',
                  'max_bps': 1200000,
                  'min_bps': 500000,
                  'live_from_start': 0,
                  'use_nexdef': 0,
                  'use_wired_web': 0,
                  'adaptive_stream': 0,
                  'coverage' : 'home',
                  'show_inning_frames': 1,
                  'use_librtmp': 0,
                  'no_lirc': 0,
                  'postseason': 0,
                  'free_condensed': 0,
                  'milbtv' : 0,
                  'rss_browser': 'firefox -new-tab %s',
                  'flash_browser': DEFAULT_FLASH_BROWSER}
    try:
        os.lstat(myconf)
    except:
        try:
            os.lstat(myconfdir)
        except:
            dir=myconfdir
        else:
            dir=None
        doinstall(myconf,mydefaults,dir)

    mycfg = MLBConfig(mydefaults)
    mycfg.loads(myconf)

    # DEFAULT_KEYBINDINGS is a dict() of default keybindings
    # found in MLBviewer/mlbDefaultKeyBindings.py rather than
    # MLBviewer/mlbConstants.py
    mykeyfile = os.path.join(myconfdir,'keybindings')
    mykeys = MLBKeyBindings(DEFAULT_KEYBINDINGS)
    mykeys.loads(mykeyfile)

    curses.wrapper(mainloop, mycfg, mykeys)


