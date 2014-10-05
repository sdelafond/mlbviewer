#!/usr/bin/env python
# coding=UTF-8

import curses
import curses.textpad
import locale
import datetime
import re
import select
import errno
import signal
import sys
import time
from math import ceil
from MLBviewer import *

locale.setlocale(locale.LC_ALL,"")

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
    mykeys.set('MEDIA_INFO','i')
    mykeys.set('ENTRY_SORT', 's')
    CFG_SPEED = int(mycfg.get('speed'))
    if CFG_SPEED >= 1800:
        mycfg.set('speed',1800)
    else:
        mycfg.set('speed',1200)

    # insurance of proper sort entry
    if mycfg.get('entry_sort') not in CLASSICS_ENTRY_SORT:
        mycfg.set('entry_sort',CLASSICS_ENTRY_SORT[0])

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

    optwin = MLBOptWin(myscr,mycfg)
    classics = MLBClassics(mycfg)
    available = []
    mlbClassicsMenu = MLBClassicsMenuWin(myscr,mycfg,available)
    mlbClassicsMenu.Splash()
    mlbClassicsPlistWin = MLBClassicsPlistWin(myscr,mycfg,available)
    optwin.statusWrite('Fetching YouTube feed and playlist data. Please wait.')
    try:
        # TODO: Handle multiple feed sources better.
        for user in mycfg.get('classics_users'):
            # this is cumulative so only the last return matters
            available = classics.getFeed(feed=user)      
    except:
        if len(available) > 0:
            pass
        optwin.statusWrite('ERROR: Could not retrieve playlist. Abort.',wait=2)
        curses.nocbreak()
        myscr.keypad(0)
        curses.echo()
        curses.endwin()
        sys.exit()
    mlbClassicsMenu.data = available
    mlbClassicsMenu.records = available[:curses.LINES-4]
    mlbClassicsList = None
    #time.sleep(1)
    mywin = mlbClassicsMenu

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
            mywin = mlbClassicsMenu
            mywin.PgUp()
            
        if c in mykeys.get('OPTIONS'):
            optwin = MLBOptWin(myscr,mycfg)
            mywin = optwin

        if c in mykeys.get('ENTRY_SORT'):
            key=CLASSICS_ENTRY_SORT.index(mycfg.get('entry_sort'))
            mycfg.set('entry_sort', CLASSICS_ENTRY_SORT[not key])
            if mywin == mlbClassicsPlistWin:
                mywin.statusWrite('Fetching playlist entries...')
                try:
                    playlist = classics.getPlaylistEntries(mlbClassicsMenu.records[mlbClassicsMenu.current_cursor]['url'])
                except:
                    raise
                    mywin.statusWrite('An error occurred retrieving playlist.',wait=2)
                    continue
                mlbClassicsPlistWin = MLBClassicsPlistWin(myscr,mycfg,playlist['entries'])
                mywin = mlbClassicsPlistWin
                mywin.current_cursor = 0
                mywin.record_cursor = 0
                continue
            continue

        if c in mykeys.get('MEDIA_INFO'):
            if mywin in ( optwin, ):
                continue
            myscr.clear()
            mywin.titlewin.clear()
            mywin.titlewin.addstr(0,0,'MEDIA INFORMATION')
            mywin.titlewin.hline(1, 0, curses.ACS_HLINE, curses.COLS-1)
            output=[]
            for k in ( 'title', 'author', 'url', 'duration', 'description' ):
                if mywin.records[mywin.current_cursor].has_key(k):
                    infoStr="%-8s: %s" % (k.upper(),
                                         mywin.records[mywin.current_cursor][k])
                    # break up string into words and break lines at word
                    # boundaries
                    tmp_str=''
                    for word in infoStr.split(' '):
                        if word.find('\n') > -1:
                            for w in word.split('\n'):
                                if w == '':
                                    output.append(tmp_str)
                                    tmp_str=''
                                elif len(tmp_str) + len(w) < (curses.COLS-2):
                                    tmp_str+=w + ' '
                                else:
                                    output.append(tmp_str)
                                    tmp_str=w + ' '
                        elif len(tmp_str) + len(word) < (curses.COLS-2):
                            tmp_str+=word + ' '
                        else:
                            output.append(tmp_str)
                            tmp_str=word + ' '
                    output.append(tmp_str)
            n=2
            for line in output:
                if n < curses.LINES-3:    
                    myscr.addstr(n,0,line)
                    n+=1
                else:
                    break
            myscr.refresh()
            mywin.titlewin.refresh()
            mywin.statusWrite('Press a key to continue...',wait=-1)

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
            if len(mywin.records) == 0:
                continue
            if mywin in ( optwin, ):
                continue
            if mywin == mlbClassicsMenu:
                mywin.statusWrite('Fetching playlist entries...')
                try:
                    playlist = classics.getPlaylistEntries(mywin.records[mywin.current_cursor]['url'])
                except:
                    raise
                    mywin.statusWrite('An error occurred retrieving playlist.',wait=2)
                    continue
                mlbClassicsPlistWin = MLBClassicsPlistWin(myscr,mycfg,playlist['entries'])
                mywin = mlbClassicsPlistWin
                mywin.current_cursor = 0
                mywin.record_cursor = 0
                continue
                
            # Video selection and playback starts here
            mediaUrl = mywin.records[mywin.current_cursor]['url']
            mediaStream = MLBClassicsStream(mediaUrl,mycfg)
            mediaUrl = mediaStream.prepareMediaStreamer(mediaUrl)
            cmdStr = mediaStream.preparePlayerCmd(mediaUrl,'MLBVIDEO','classics')
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
                  'classics_users': ['MLBClassics', 'ClassicMLB11', 'TheMLBhistory', 'TheBaseballHall', 'PhilliesClassics'],
                  'entry_sort' : 'title',
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


