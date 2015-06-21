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
#    fp.write('# See README for explanation of these settings.\n')
#    fp.write('# user and pass are required except for Top Plays\n')
#    fp.write('user=\n')
#    fp.write('pass=\n\n')
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
#    print
#    print 'Configuration complete!  You are now ready to use mlbviewer.'
#    print
#    print 'Configuration file written to: '
#    print
#    print config
#    print
#    print 'Please review the settings.  You will need to set user and pass.'
#    sys.exit()

def mainloop(myscr,mycfg,mykeys):

    # some initialization
    log = open(LOGFILE, "a")
    DISABLED_FEATURES = []
    # add in a keybinding for listings that makes sense, e.g. Menu
    mykeys.set('LISTINGS','m')

    # not sure if we need this for remote displays but couldn't hurt

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


    stats = MLBStats(mycfg)
    optwin = MLBOptWin(myscr,mycfg)
    helpwin = MLBStatsHelpWin(myscr,mykeys)
    try:
        stats.getStatsData()
    except KeyError:
        raise Exception,stats.url
    statwin = MLBStatsWin(myscr,mycfg,stats.data,stats.last_update)
    mywin = statwin

    mywin.titleRefresh()

    while True:
        myscr.clear()
        try:
            mywin.Refresh()
        except:
            raise
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

        if c in mykeys.get('DOWN'):
            mywin.Down()

        if c in mykeys.get('HELP'):
            mywin = helpwin

        if c in mykeys.get('HITTING'):
            mycfg.set('player_id', 0)
            mycfg.set('stat_type','hitting')
            mycfg.set('sort_column','avg')
            statwin.statusWrite('Refreshing statistics...')
            stats.getStatsData()
            statwin.data = stats.data
            mywin = statwin

        if c in mykeys.get('PITCHING'):
            mycfg.set('player_id', 0)
            mycfg.set('stat_type','pitching')
            mycfg.set('sort_column','era')
            statwin.statusWrite('Refreshing statistics...')
            stats.getStatsData()
            statwin.data = stats.data
            mywin = statwin

        if c in mykeys.get('PLAYER'):
            if mywin in ( helpwin, optwin ):
                continue
            if len(statwin.records) == 0:
                continue
            if int(mycfg.get('player_id')) > 0:
                mycfg.set('player_id', 0)
            else:
                mycfg.set('player_id',int(statwin.records[statwin.current_cursor]['player_id']))
                mycfg.set('player_name',statwin.records[statwin.current_cursor]['name_display_first_last'])
            statwin.statusWrite('Refreshing statistics...')
            stats.getStatsData()
            statwin.data = stats.data
            statwin.PgUp()
            mywin = statwin

        if c in mykeys.get('STATS_DEBUG'):
            myscr.clear()
            mywin.titlewin.clear()
            try:
                name = statwin.records[statwin.current_cursor]['name_display_last_init']
            except:
                name = mycfg.get('player_id')
            mywin.titlewin.addnstr(0,0,'STATS DEBUG FOR %s' % name, curses.COLS-2)
            mywin.titlewin.hline(1,0, curses.ACS_HLINE,curses.COLS-1)
            myscr.addstr(3,0,repr(statwin.records[statwin.current_cursor]))
            myscr.refresh()
            mywin.titlewin.refresh()
            mywin.statusWrite('Press a key to continue...',wait=-1)
            mywin = statwin
 
        if c in mykeys.get('URL_DEBUG'):
            myscr.clear()
            mywin.titlewin.clear()
            mywin.titlewin.addstr(0,0,'URL DEBUG')
            mywin.titlewin.hline(1,0, curses.ACS_HLINE,curses.COLS-1)
            myscr.addnstr(3,0,'Stats settings:',curses.COLS-2)
            myscr.addstr(4,0,repr(mycfg.data))
            if curses.LINES > 15:
                myscr.addnstr(11,0,'URL for current query:',curses.COLS-2)
                myscr.addstr(12,0,repr(stats.url))
            myscr.refresh()
            mywin.titlewin.refresh()
            mywin.statusWrite('Press a key to continue...',wait=-1)
            mywin = statwin

        if c in mykeys.get('DEBUG'):
            if mycfg.get('debug'):
                mycfg.set('debug', False)
            else:
                mycfg.set('debug', True)
            mywin = statwin

        # SCREENS
        if c in mykeys.get('SORT'):
            sortPrompt = 'Enter column to sort on: '
            sortOrder = statwin.prompter(statwin.statuswin, sortPrompt).strip()
            #sortOrder = sortOrder.strip()
            if sortOrder.lower() == '2b':
                sortOrder = 'd'
            if sortOrder.lower() == '3b':
                sortOrder = 't'
            if sortOrder not in statwin.records[statwin.current_cursor].keys():
                statwin.statusWrite('Invalid sort key!',wait=1)
                continue
            stats.sort = sortOrder.lower()
            mycfg.set('sort_column',stats.sort)
            statwin.statusWrite('Refreshing statistics...')
            stats.getStatsData()
            statwin.data = stats.data
            mywin = statwin

        if c in mykeys.get('TEAM'):
            # build a reverse dictionary of teamcode to id
            tmp = dict()
            for t in STATS_TEAMS.keys():
                tmp[STATS_TEAMS[t]] = t
            teamPrompt = "Enter teamcode to sort on (or 'mlb' for all): "
            teamCode = statwin.prompter(statwin.statuswin, teamPrompt).strip()
            if teamCode not in tmp.keys():
                statwin.statusWrite('Invalid team code!',wait=1)
                continue
            statwin.statusWrite('Refreshing statistics...')
            mycfg.set('sort_team',tmp[teamCode])
            stats.getStatsData()
            statwin.data = stats.data
            mywin = statwin
            
        if c in mykeys.get('LEAGUE'):
            try:
                tmp = STATS_LEAGUES.index(mycfg.get('league'))
            except:
                mywin.statusWrite('Invalid league value, defaulting to MLB',wait=1)
                mycfg.set('league','MLB')
                continue
            tmp = ( tmp + 1 ) % len(STATS_LEAGUES)
            mycfg.set('league', STATS_LEAGUES[tmp])
            statwin.statusWrite('Refreshing statistics...')
            stats.getStatsData()
            statwin.data = stats.data
            mywin = statwin

        if c in mykeys.get('YEAR'):
            year_prompt = "Year? [YYYY]: "
            query = statwin.prompter(statwin.statuswin,year_prompt).strip()
            try:
                year = time.strptime(query,"%Y").tm_year
            except:
                if query == '':
                    statwin.statusWrite('Changing to current year...',wait=1)
                    year = datetime.datetime.now().year
                else:
                    statwin.statusWrite('Invalid year format.',wait=2)
                    continue
            mycfg.set('season_type','ANY')
            mycfg.set('season',year)
            statwin.statusWrite('Refreshing statistics...')
            stats.getStatsData()
            statwin.data = stats.data

        if c in mykeys.get('SEASON_TYPE'):
            try:
                tmp = STATS_SEASON_TYPES.index(mycfg.get('season_type'))
            except:
                tmp = -1
            tmp = ( tmp + 1 ) % len(STATS_SEASON_TYPES)
            mycfg.set('season_type', STATS_SEASON_TYPES[tmp])
            statwin.statusWrite('Refreshing statistics...')
            stats.getStatsData()
            statwin.data = stats.data
            mywin = statwin

        if c in mykeys.get('ACTIVE'):
            # it's a boolean. just flip the bit
            try:
                tmp = int(mycfg.get('active_sw'))
            except ValueError:
                # flip to a sensible default
                tmp = 1
            tmp ^= 1
            mycfg.set('active_sw',tmp)
            statwin.statusWrite('Refreshing statistics...')
            stats.getStatsData()
            statwin.data = stats.data
            mywin = statwin

        if c in mykeys.get('SORT_ORDER'):
            try:
                tmp = int(mycfg.get('sort_order'))
            except:
                tmp = -1
            tmp = ( tmp + 1 ) % 3
            #mycfg.set('sort_order',STATS_SORT_ORDER[tmp])
            mycfg.set('sort_order',tmp)
            statwin.statusWrite('Refreshing statistics...')
            stats.getStatsData()
            statwin.data = stats.data
            mywin = statwin


        if c in mykeys.get('QUIT'):
            curses.nocbreak()
            myscr.keypad(0)
            curses.echo()
            curses.endwin()
            break

if __name__ == "__main__":
    myconfdir = os.path.join(os.environ['HOME'],AUTHDIR)
    myconf =  os.path.join(myconfdir,STATFILE)
    mydefaults = {'stat_type': 'pitching',
                  'sort_column': 'era',
                  'sort_order': 0,
                  'league': 'MLB',
                  'sort_team': 0,
                  'player_pool': 'QUALIFIER',
                  'player_id': 0,
                  'active_sw': 0,
                  'use_color': 0,
                  'favorite_color': 'cyan',
                  'favorite': [],
                  'bg_color': 'xterm',
                  'season_type': 'ANY',
                  'active_sw': 0,
                  'season': datetime.datetime.now().year,
                  'curses_debug': 0,
                  'wiggle_timer': 0.5,
                  'sort_order': 0,
                  'time_offset': '',
                  'triple_crown': 0,
                  'debug': 0, }
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

    # STATS_KEYBINDINGS is a dict() of default keybindings
    # found in MLBviewer/mlbStatsKeyBindings.py rather than
    # MLBviewer/mlbConstants.py
    mykeyfile = os.path.join(myconfdir,'keybindings')
    mykeys = MLBKeyBindings(STATS_KEYBINDINGS)
    mykeys.loads(mykeyfile)

    curses.wrapper(mainloop, mycfg, mykeys)


