#!/usr/bin/env python

import curses
import curses.textpad
import datetime
import time
import calendar
import re
import select
import errno
import signal
import sys
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

def prompter(win,prompt):
    win.clear()
    win.addstr(0,0,prompt,curses.A_BOLD)
    win.refresh()

    responsewin = win.derwin(0, len(prompt))
    responsebox = curses.textpad.Textbox(responsewin)
    responsebox.edit()
    output = responsebox.gather()

    return output

def timeShiftOverride(time_shift=None,reverse=False):
    try:
        plus_minus=re.search('[+-]',time_shift).group()
        (hrs,min)=time_shift[1:].split(':')
        offset=datetime.timedelta(hours=int(plus_minus + hrs), minutes=int(min))
        offset=(offset,offset*-1)[reverse]
    except:
        offset=datetime.timedelta(0,0)
    return offset


def mainloop(myscr,mycfg,mykeys):

    # some initialization
    log = open(LOGFILE, "a")
    DISABLED_FEATURES = []
    RESTORE_SPEED = mycfg.get('speed')

    # not sure if we need this for remote displays but couldn't hurt
    if mycfg.get('x_display'):
        os.environ['DISPLAY'] = mycfg.get('x_display')

    try:
        curses.curs_set(0)
    except curses.error:
        pass

    # mouse events
    if mycfg.get('enable_mouse'):
        curses.mousemask(1)

    # initialize the color settings
    if hasattr(curses, 'use_default_colors'):
        try:
            curses.use_default_colors()
            if mycfg.get('use_color'):
                try:
                    if mycfg.get('fg_color'):
                        mycfg.set('favorite_color', mycfg.get('fg_color'))
                    if mycfg.get('free_color') is None:
                        mycfg.set('free_color', COLORS['green'])
                    curses.init_pair(COLOR_FAVORITE, 
                                     COLORS[mycfg.get('favorite_color')],
                                     COLORS[mycfg.get('bg_color')])
                    curses.init_pair(COLOR_FREE, 
                                     COLORS[mycfg.get('free_color')],
                                     COLORS[mycfg.get('bg_color')])
                    curses.init_pair(COLOR_DIVISION,
                                     COLORS[mycfg.get('division_color')],
                                     COLORS[mycfg.get('bg_color')])
                except KeyError:
                    mycfg.set('use_color', False)
                    curses.init_pair(1, -1, -1)
        except curses.error:
            pass

    # initialize the input
    inputlst = [sys.stdin]

    available = []
    listwin = MLBListWin(myscr,mycfg,available)
    if SPEEDTOGGLE.get(RESTORE_SPEED) is None:
        listwin.statusWrite("Invalid speed.  Switching to 1200...",wait=2)
        mycfg.set('speed','1200')
    topwin = MLBTopWin(myscr,mycfg,available)
    optwin = MLBOptWin(myscr,mycfg)
    helpwin = MLBHelpWin(myscr,mykeys)
    rsswin = MLBRssWin(myscr,mycfg)
    postwin = None
    sbwin = None
    linewin = None
    boxwin = None
    stdwin = None
    calwin = None
    statwin = None
    detailwin = None
    stats = MLBStats(mycfg)
    # initialize some variables to re-use for 304 caching
    boxscore = None
    linescore = None
    standings = None

    # now it's go time!
    mywin = listwin
    mywin.Splash()
    mywin.statusWrite('Logging into mlb.com...',wait=0)
    
    session = MLBSession(user=mycfg.get('user'),passwd=mycfg.get('pass'),
                         debug=mycfg.get('debug'))
    try:
        session.getSessionData()
    except MLBAuthError:
        error_str = 'Login was unsuccessful.  Check user and pass in ' + myconf
        mywin.statusWrite(error_str,wait=2)
    except Exception,detail:
        error_str = str(detail)
        mywin.statusWrite(error_str,wait=2)

    mycfg.set('cookies', {})
    mycfg.set('cookies', session.cookies)
    mycfg.set('cookie_jar' , session.cookie_jar)
    try:
        log.write('session-key from cookie file: '+session.cookies['ftmu'] +\
                  '\n')
    except:
        log.write('no session-key found in cookie file\n')

    # Listings
    mlbsched = MLBSchedule(ymd_tuple=startdate,
                          time_shift=mycfg.get('time_offset'),
                          use_wired_web=mycfg.get('use_wired_web'))
    milbsched = MiLBSchedule(ymd_tuple=startdate,
                             time_shift=mycfg.get('time_offset'))
    # default to MLB.TV
    mysched = mlbsched
    # We'll make a note of the date, to return to it later.
    today_year = mlbsched.year
    today_month = mlbsched.month
    today_day = mlbsched.day

    try:
        available = mysched.getListings(mycfg.get('speed'),
                                        mycfg.get('blackout'))
    except (KeyError, MLBXmlError,MLBUrlError), detail:
        if mycfg.get('debug'):
            #raise Exception, detail
            raise
        else:
            listwin.statusWrite(mysched.error_str,wait=2)
        available = []

    mywin.data = available
    mywin.records = available[0:curses.LINES-4]
    mywin.titleRefresh(mysched)

    # If favorite is not none, focus the cursor on favorite team
    if mycfg.get('favorite') is not None:
        try:
            favorite=mycfg.get('favorite')
            for f in favorite:
                for follow in ( 'audio_follow', 'video_follow' ):
                    if f not in mycfg.get(follow) and not mycfg.get('disable_favorite_follow'):
                        mycfg.set(follow, f)
            mywin.focusFavorite()
        except IndexError:
            raise Exception,repr(mywin.records)
    
    # PLACEHOLDER - LircConnection() goes here

    while True:
        myscr.clear()

        try:
            mywin.Refresh()
        except MLBCursesError,detail:
            mywin.titleRefresh(mysched)
            mywin.statusWrite("ERROR: %s"%detail,wait=2)
        except IndexError:
            raise Exception,"current_cursor=%s, record_cursor=%s, cl-4=%s, lr=%s,ld=%s" %\
                (mywin.current_cursor,mywin.record_cursor,curses.LINES-4,len(mywin.records),len(mywin.data) )
        mywin.titleRefresh(mysched)
        #pass prefer to statusRefresh but first work it out
        #mywin.statusRefresh()
        if mywin in ( listwin, sbwin, detailwin ):
            try:
                prefer = mysched.getPreferred(
                    listwin.records[listwin.current_cursor], mycfg)
            except IndexError:
                # this can fail if mlbsched.getSchedule() fails
                # that failure already prints out an error, so skip this
                pass
        elif mywin == postwin:
            try:
                prefer['video'] = mywin.records[mywin.current_cursor][2] 
            except:
                prefer['video'] = None
        if mywin in ( detailwin, ):
            mywin.statusRefresh(prefer=prefer)
        else:
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
                listwin.resize()
                if mywin in ( sbwin, detailwin ):
                    # align the cursors between scoreboard and listings
                    mywin.setCursors(listwin.record_cursor, 
                                     listwin.current_cursor)
                continue
        
        if sys.stdin in inputs:
            c = myscr.getch()

        # MOUSE HANDLING
        # Right now, only clicking on a listwin listing will act like a 
        # VIDEO keypress.
        # TODO:
        # Check x,y values to see handle some of the toggles.
        # Might even overload the "Help" region of interface to allow a 
        # mouse-friendly overlay.
        # Use a cfg setting to disable mouse support altogether so users 
        # clicking on the window to raise it won't get unexpected results.
        if c == curses.KEY_MOUSE:
            if mywin != listwin:
                continue
            id, mousex, mousey, mousez, bstate  = curses.getmouse()
            #mywin.statusWrite("mx = %s, my = %s, cc=%s, lr=%s"%(mousex,mousey,listwin.current_cursor,len(listwin.records)),wait=1)
            mousecursor = mousey - 2
            if mousey < 2:
                continue
            if mousecursor < len(listwin.records):
                try:
                    prefer = mysched.getPreferred(listwin.records[mousey-2], 
                                                  mycfg)
                except IndexError:
                    continue
                else:
                    listwin.current_cursor = mousecursor
                    # If mouse clicked on a valid listing, push the event
                    # back to getch() as a VIDEO keypress.
                    curses.ungetch(mykeys.get('VIDEO')[0])
            else:
                continue

        # NAVIGATION
        if c in mykeys.get('UP'):
            if mywin in ( sbwin , detailwin ):
                listwin.Up()
            mywin.Up()
        
        if c in mykeys.get('DOWN'):
            if mywin in ( sbwin , detailwin ):
                listwin.Down()
            mywin.Down()

        # TODO: haven't changed this binding but probably won't
        if c in ('Page Down', curses.KEY_NPAGE):
            mywin.PgDown()

        # TODO: haven't changed this binding but probably won't
        if c in ('Page Up', curses.KEY_PPAGE):
            mywin.PgUp()

        if c in mykeys.get('JUMP'):
            if mywin not in ( listwin, sbwin, calwin, detailwin ):
                continue
            jump_prompt = 'Date (m/d/yy)? '
            if datetime.datetime(mysched.year,mysched.month,mysched.day) <> \
                    datetime.datetime(today_year,today_month,today_day):
                jump_prompt += '(<enter> returns to today) '
            query = listwin.prompter(listwin.statuswin, jump_prompt)
            # Special case. If the response is blank, we jump back to
            # today.
            if query == '':
                listwin.statusWrite('Jumping back to today',wait=1)
                listwin.statusWrite('Refreshing listings...',wait=1)
                # Really jump to today and not mlbsched date
                now = datetime.datetime.now()
                dif = datetime.timedelta(1)
                if now.hour < 9:
                    now = now - dif
                ymd_tuple = (now.year, now.month, now.day)
                try:
                    available = mysched.Jump(ymd_tuple,
                                             mycfg.get('speed'),
                                             mycfg.get('blackout'))
                    listwin.data = available
                    listwin.records = available[0:curses.LINES-4]
                    listwin.record_cursor = 0
                    listwin.current_cursor = 0
                    listwin.focusFavorite()
                except (KeyError,MLBXmlError),detail:
                    if mycfg.get('debug'):
                        raise Exception,detail
                    available = []
                    listwin.data = []
                    listwin.records = []
                    listwin.current_cursor = 0
                    if mywin != calwin:
                        listwin.statusWrite("There was a parser problem with the listings page",wait=2)
                        mywin = listwin
                        continue
                # recreate calendar if current screen
                if mywin == calwin:
                    calwin.Jump(ymd_tuple)
                    continue
                # recreate master scoreboard if current screen
                elif mywin in ( sbwin, ):
                    GAMEID = listwin.records[listwin.current_cursor][6]
                    if sbwin in ( None, [] ):
                        sbwin = MLBMasterScoreboardWin(myscr,mycfg,GAMEID)
                    try:
                        sbwin.getScoreboardData(GAMEID)
                    except MLBUrlError:
                        sbwin.statusWrite(self.error_str,wait=2)
                        continue
                    # align the cursors between scoreboard and listings
                    sbwin.setCursors(listwin.record_cursor, 
                                     listwin.current_cursor)
                    mywin = sbwin
                elif mywin == detailwin:
                    game=listwin.records[listwin.current_cursor]
                    gameid=game[6]
                    detail = MLBMediaDetail(mycfg,listwin.data)
                    games = detail.parseListings()
                    detailwin = MLBMediaDetailWin(myscr,mycfg,gameid,games)
                    detailwin.getMediaDetail(gameid)
                    mywin = detailwin
                    mywin.setCursors(listwin.record_cursor, 
                                     listwin.current_cursor)
                continue
            try:
                # Try 4-digit year first
                jumpstruct=time.strptime(query.strip(),'%m/%d/%Y')
            except ValueError:
                try:
                    # backwards compatibility 2-digit year?
                    jumpstruct=time.strptime(query.strip(),'%m/%d/%y')
                except ValueError:
                    listwin.statusWrite("Date not in correct format",wait=2)
		    continue
            listwin.statusWrite('Refreshing listings...')
            mymonth = jumpstruct.tm_mon
            myday = jumpstruct.tm_mday
            myyear = jumpstruct.tm_year
            try:
                available = mysched.Jump((myyear, mymonth, myday),
                                          mycfg.get('speed'),
                                          mycfg.get('blackout'))
                listwin.data = available
                listwin.records = available[0:curses.LINES-4]
                listwin.record_cursor = 0
                listwin.current_cursor = 0
                listwin.focusFavorite()
            except (KeyError,MLBXmlError,MLBUrlError),detail:
                if mycfg.get('debug'):
                    raise Exception,detail
                available = []
                listwin.statusWrite("There was a parser problem with the listings page",wait=2)
                listwin.data = []
                listwin.records = []
                listwin.current_cursor = 0
            # recreate calendar if current screen
            if mywin == calwin:
                calwin.Jump((myyear,mymonth,myday))
                continue
            # recreate master scoreboard if current screen
            elif mywin in ( sbwin, ):
                GAMEID = listwin.records[listwin.current_cursor][6]
                if sbwin in ( None, [] ):
                    sbwin = MLBMasterScoreboardWin(myscr,mycfg,GAMEID)
                try:
                    sbwin.getScoreboardData(GAMEID)
                except MLBUrlError:
                    sbwin.statusWrite(self.error_str,wait=2)
                    continue
                sbwin.setCursors(listwin.record_cursor, 
                                 listwin.current_cursor)
                mywin = sbwin
            elif mywin == detailwin: 
                game=listwin.records[listwin.current_cursor]
                gameid=game[6]
                detail = MLBMediaDetail(mycfg,listwin.data)
                games = detail.parseListings()
                detailwin = MLBMediaDetailWin(myscr,mycfg,gameid,games)
                detailwin.getMediaDetail(gameid)
                mywin = detailwin
                mywin.setCursors(listwin.record_cursor, 
                                 listwin.current_cursor)

        if c in mykeys.get('LEFT') or c in mykeys.get('RIGHT'):
            if mywin not in ( listwin, sbwin, linewin, calwin, detailwin ):
                continue
            if mywin in ( listwin, sbwin, calwin, detailwin ):
                listwin.statusWrite('Refreshing listings...')
            # handle linescore separately - this is for scrolling through 
            # extra innings - calendar navigation is also different
            if mywin in ( linewin, calwin ):
                if c in mykeys.get('LEFT'):
                    mywin.Left()
                else:
                    mywin.Right()
                continue
            try:
                if c in mykeys.get('LEFT'):
                    available = mysched.Back(mycfg.get('speed'), 
                                             mycfg.get('blackout'))
                else:
                    available = mysched.Forward(mycfg.get('speed'), 
                                                mycfg.get('blackout'))
            except (KeyError, MLBXmlError, MLBUrlError), detail:
                if mycfg.get('debug'):
                    raise Exception,detail
                available = []
                status_str = "There was a parser problem with the listings page"
                mywin.statusWrite(status_str,wait=2)
            listwin.data = available
            listwin.records = available[0:curses.LINES-4]
            listwin.current_cursor = 0
            listwin.record_cursor = 0
            listwin.focusFavorite()
            # recreate the master scoreboard view if current screen
            if mywin in ( sbwin, ):
                try:
                    GAMEID = listwin.records[listwin.current_cursor][6]
                except IndexError:
                    sbwin.sb = []
                    continue
                if sbwin in ( None, [] ):
                    sbwin = MLBMasterScoreboardWin(myscr,mycfg,GAMEID)
                try:
                    sbwin.getScoreboardData(GAMEID)
                except MLBUrlError:
                    sbwin.statusWrite(self.error_str,wait=2)
                    continue
                sbwin.setCursors(listwin.record_cursor, 
                                 listwin.current_cursor)
                mywin = sbwin
            elif mywin in ( detailwin, ):
                game=listwin.records[listwin.current_cursor]
                gameid=game[6]
                detail = MLBMediaDetail(mycfg,listwin.data)
                games = detail.parseListings()
                detailwin = MLBMediaDetailWin(myscr,mycfg,gameid,games)
                detailwin.getMediaDetail(gameid)
                mywin = detailwin
                mywin.setCursors(listwin.record_cursor, 
                                 listwin.current_cursor)

        # DEBUG : NEEDS ATTENTION FOR SCROLLING
        if c in mykeys.get('MEDIA_DEBUG'):
            if mywin in ( optwin, helpwin, stdwin ):
                continue
            if mywin == topwin:
                try:
                    gameid = mywin.records[topwin.current_cursor][4]
                except IndexError:
                    listwin.statusWrite("No media debug available.",wait=2)
                    continue
            elif mywin == calwin:
                try:
                    gameid = mywin.gamedata[mywin.game_cursor][0]
                except IndexError:
                    mywin.statusWrite("No media debug available.",wait=2)
                    continue
            elif mywin in ( rsswin, boxwin ):
                if mywin == boxwin:
                    title_str="BOX SCORE LINE DEBUG"
                else:
                    title_str="RSS ELEMENT DEBUG"
                try:
                    myscr.clear()
                    mywin.titlewin.addstr(0,0,title_str)
                    mywin.titlewin.hline(1, 0, curses.ACS_HLINE, curses.COLS-1)
                    myscr.addstr(2,0,repr(mywin.records[mywin.current_cursor]))
                    myscr.refresh()
                    mywin.titlewin.refresh()
                    mywin.statusWrite('Press a key to continue...',wait=-1)
                    continue
                except:
                    raise
            else:
                try:
                    gameid = listwin.records[listwin.current_cursor][6]
                except IndexError:
                    listwin.statusWrite("No media debug available.",wait=2)
                    continue
            myscr.clear()
            mywin.titlewin.clear()
            mywin.titlewin.addnstr(0,0,'LISTINGS DEBUG FOR ' + gameid,
                                       curses.COLS-2)
            mywin.titlewin.hline(1, 0, curses.ACS_HLINE, curses.COLS-1)
            myscr.addnstr(2,0,'getListings() for current_cursor:',curses.COLS-2)
            if mywin in ( sbwin , boxwin, detailwin ):
                myscr.addstr(3,0,repr(listwin.records[listwin.current_cursor]))
            elif mywin in ( calwin, ):
                myscr.addnstr(3,0,repr(calwin.gamedata[calwin.game_cursor]),
                              (curses.LINES-4)*(curses.COLS)-1)
            else:
                myscr.addstr(3,0,repr(mywin.records[mywin.current_cursor]))
            # hack for scrolling - don't display these lines if screen too
            # small
            if curses.LINES-4 > 14 and mywin not in ( calwin, statwin ):
                myscr.addstr(11,0,'preferred media for current cursor:')
                myscr.addstr(12,0,repr(prefer))
            myscr.refresh()
            mywin.titlewin.refresh()
            mywin.statusWrite('Press a key to continue...',wait=-1)

        # MEDIA DETAIL
        if c in mykeys.get('MEDIA_DETAIL'):
            game=listwin.records[listwin.current_cursor]
            gameid=game[6]
            detail = MLBMediaDetail(mycfg,listwin.data)
            games = detail.parseListings()
            detailwin = MLBMediaDetailWin(myscr,mycfg,gameid,games)
            detailwin.getMediaDetail(gameid)
            mywin = detailwin
            detailwin.setCursors(listwin.record_cursor, 
                             listwin.current_cursor)

        # SCREENS - NEEDS WORK FOR SCROLLING
        if c in mykeys.get('HELP'):
            helpwin = MLBHelpWin(myscr,mykeys)
            mywin = helpwin
            #mywin.helpScreen()

        # postseason
        if c in mykeys.get('POSTSEASON'):
            if mywin not in ( listwin, sbwin ):
                continue
            try:
                event_id = listwin.records[listwin.current_cursor][2][0][3]
            except:
                mywin.statusWrite('No postseason angles available.',wait=1)
                continue
            mywin.statusWrite('Retrieving postseason camera angles...')
            try:
                cameras = mysched.getMultiAngleListing(event_id)
            except:
                cameras = []
            postwin = MLBPostseason(myscr,mycfg,cameras)
            mywin = postwin

        # NEEDS ATTENTION FOR SCROLLING
        if c in mykeys.get('OPTIONS'):
            optwin = MLBOptWin(myscr,mycfg)
            mywin = optwin

        if c in mykeys.get('STATS'):
            # until I have triple crown stats implemented, point them at 
            # the mlbstats app
            mywin.statusWrite('See mlbstats.py for statistics.',wait=2)
            continue
            if mycfg.get('milbtv'):
                mywin.statusWrite("Stats are not supported for MiLB",wait=2)
                continue
            mywin.statusWrite('Retrieving stats...')
            mycfg.set('league','MLB')
            if mycfg.get('stat_type') is None or mycfg.get('stat_type') == 'hitting':
                mycfg.set('stat_type','pitching')
                mycfg.set('sort_column','era')
            else:
                mycfg.set('stat_type','hitting')
                mycfg.set('sort_column','avg')
            mycfg.set('player_id',0)
            mycfg.set('sort_team',0)
            mycfg.set('active_sw',0)
            mycfg.set('season_type','ANY')
            mycfg.set('sort_order','default')
            try:
                stats.getStatsData()
            except MLBUrlError:
                raise
            statwin = MLBStatsWin(myscr,mycfg,stats.data,stats.last_update)
            mywin=statwin
            
        if c in mykeys.get('STANDINGS'):
            if mycfg.get('milbtv'):
                mywin.statusWrite('Standings are not supported for MiLB',wait=2)
                continue
            mywin.statusWrite('Retrieving standings...')
            if standings is None:
                standings = MLBStandings()
            try:
                (year, month, day) = (mysched.year, mysched.month, mysched.day)
                log.write('getStandingsData((%s,%s,%s))\n'%(year, month, day))
                log.flush()
                standings.getStandingsData((year,month,day))
            except MLBUrlError:
                mywin.statusWrite(standings.error_str,wait=2)
                continue
            stdwin = MLBStandingsWin(myscr,mycfg,standings.data,
                                     standings.last_update,year)
            mywin = stdwin

        if c in mykeys.get('RSS'):
            if mywin == rsswin:
                rsswin.getFeedFromUser()
                continue
            rsswin.data = []
            feeds = []
            if len(mycfg.get('favorite')) > 0:
                for team in mycfg.get('favorite'):
                    if team in TEAMCODES.keys():
                        feeds.append(team)
                if len(feeds) < 1:
                    feeds.append('mlb')
            else:
                feeds.append('mlb')
            for team in feeds:
                rsswin.getRssData(team=team)
            mywin = rsswin

        if c in mykeys.get('CALENDAR'):
            if mycfg.get('milbtv'):
                # for now, not going to support calendar for milb
                mywin.statusWrite('Calendar not supported for MiLB.',wait=2)
                continue
            ( year, month ) = ( None, None )
            if mywin not in ( calwin, ):
                if len(mycfg.get('favorite')) > 0:
                    team = mycfg.get('favorite')[0]
                else:
                    team = 'ana'
                try:
                    year = mysched.year
                    month = mysched.month
                except IndexError:
                    now=datetime.datetime.now()
                    year = now.year
                    month = now.month
            else:
                team = calwin.getTeamFromUser()
                year = calwin.year
                month = calwin.month
            if team is None:
                continue
            try:
                teamid = int(TEAMCODES[team][0])
            except:
                teamid = int(TEAMCODES['ana'][0])
            mywin.statusWrite('Retrieving calendar for %s %s %s...' % \
                             (team.upper(), calendar.month_name[month], year ) )
            if calwin is None:
                calwin = MLBCalendarWin(myscr,mycfg)
            calwin.getData(teamid,year,month)
            mywin = calwin
            
            
        if c in mykeys.get('MASTER_SCOREBOARD'):
            # weird statwin crash related to window resizing
            if mywin == statwin:
                try:
                    sbwin.statusRefresh()
                    sbwin.titleRefresh()
                    sbwin.Refresh()
                    mywin = sbwin
                except:
                    mywin = listwin
            if mycfg.get('milbtv'):
                # for now, not going to support master scoreboard for milb
                mywin.statusWrite('Master scoreboard not supported for MiLB.',wait=2)
                continue
                #mycfg.set('milbtv', False)
                #listwin.PgUp()
            if mywin == calwin:
                prefer = calwin.alignCursors(mysched,listwin)
            try:
                GAMEID = listwin.records[listwin.current_cursor][6]
            except IndexError:
                mywin.statusWrite("No games today.  Cannot switch to master scoreboard from here.",wait=2)
                continue
            mywin.statusWrite('Retrieving master scoreboard for %s...' % GAMEID)
            if sbwin in ( None, [] ):
                sbwin = MLBMasterScoreboardWin(myscr,mycfg,GAMEID)
            try:
                sbwin.getScoreboardData(GAMEID)
            except MLBUrlError:
                sbwin.statusWrite(sbwin.error_str,wait=2)
                continue
            sbwin.setCursors(listwin.record_cursor, 
                             listwin.current_cursor)
            mywin = sbwin
            # And also refresh the listings
            listwin.statusWrite('Refreshing listings...',wait=1)

            try:
                available = mysched.getListings(mycfg.get('speed'),
                                                mycfg.get('blackout'))
            except:
                pass
            listwin.data = available
            listwin.records = available[listwin.record_cursor:listwin.record_cursor+curses.LINES-4]

        if c in mykeys.get('BOX_SCORE'):
            if len(mywin.records) == 0:
                continue
            elif mywin == calwin and len(calwin.gamedata) == 0:
                continue
            if mywin in ( stdwin, statwin ):
                continue
            if mywin in ( calwin, ):
                GAMEID = calwin.gamedata[calwin.game_cursor][0]
                prefer = calwin.alignCursors(mysched,listwin)
            elif mywin == linewin:
                GAMEID = linewin.data['game']['id']
            else:
                try:
                    GAMEID = listwin.records[listwin.current_cursor][6]
                except IndexError:
                    mywin.statusWrite('Listings out of sync. Please refresh.',wait=2)
                    continue
            mywin.statusWrite('Retrieving box score for %s...' % GAMEID)
            if boxscore in ( None, [] ):
                boxscore=MLBBoxScore(GAMEID)
            try:
                data = boxscore.getBoxData(GAMEID)
            except MLBUrlError:
                listwin.statusWrite(boxscore.error_str,wait=2)
                continue
            boxwin = MLBBoxScoreWin(myscr,mycfg,data)
            mywin = boxwin

        if c in mykeys.get('LINE_SCORE'):
            if len(mywin.records) == 0:
                continue
            elif mywin == calwin and len(calwin.gamedata) == 0:
                continue
            if mywin in ( stdwin, ):
                continue
            if mywin in ( calwin, ):
                GAMEID = calwin.gamedata[calwin.game_cursor][0]
                prefer = calwin.alignCursors(mysched,listwin)
            elif mywin == boxwin:
                GAMEID = boxwin.boxdata['game']['game_id']
            else:
                try:
                    GAMEID = listwin.records[listwin.current_cursor][6]
                except IndexError:
                    mywin.statusWrite('Listings out of sync. Please refresh.',wait=2)
                    continue
            mywin.statusWrite('Retrieving linescore for %s...' % GAMEID)
            # TODO: might want to embed linescore code in MLBLineScoreWin
            # and create a MLBLineScoreWin.getLineData() method like scoreboard
            if linescore in ( None, ):
                linescore = MLBLineScore(GAMEID)
            try:
                data = linescore.getLineData(GAMEID)
            except MLBUrlError:
                listwin.statusWrite(linescore.error_str,wait=2)
                continue
            linewin = MLBLineScoreWin(myscr,mycfg,data)
            mywin = linewin

        if c in mykeys.get('HIGHLIGHTS'):
            if mywin in ( optwin, helpwin, stdwin ):
                continue
            try:
                GAMEID = listwin.records[listwin.current_cursor][6]
            except IndexError:
                continue
            topwin = MLBTopWin(myscr,mycfg,available)
            topwin.data = listwin.records
            listwin.statusWrite('Fetching Top Plays list...')
            try:
                if mywin == calwin:
                    prefer = calwin.alignCursors(mysched,listwin)
                available = mysched.getTopPlays(GAMEID)
            except:
                if mycfg.get('debug'):
                    raise
                listwin.statusWrite('Could not fetch highlights.',wait=2)
                available = listwin.data
                continue
            mywin = topwin
            mywin.current_cursor = 0
            mywin.data = available
            mywin.records = available[0:curses.LINES-4]
            mywin.record_cursor = 0

        if c in mykeys.get('HIGHLIGHTS_PLAYLIST'):
            if mywin in ( optwin, helpwin, stdwin ):
                continue
            try:
                GAMEID = listwin.records[listwin.current_cursor][6]
            except IndexError:
                listwin.statusWrite('Could not find gameid for highlights',wait=2)
                continue
            listwin.statusWrite('Creating Top Plays Playlist...')
            try:
                temp = mysched.getTopPlays(GAMEID)
            except:
                listwin.statusWrite('Could not build highlights playlist.',wait=2)
            fp = open(HIGHLIGHTS_LIST, 'w')
            for highlight in temp:
                fp.write(highlight[2]+'\n')
            fp.close()
            mediaUrl = '-playlist %s' % HIGHLIGHTS_LIST
            eventId = listwin.records[listwin.current_cursor][6]
            streamtype = 'highlight'
            mediaStream = MediaStream(prefer['video'], session, mycfg,
                                      prefer['video'][1], 
                                      streamtype=streamtype)
            cmdStr = mediaStream.preparePlayerCmd(mediaUrl, eventId,streamtype)
            # NEEDS ATTENTION FOR SCROLLING
            if mycfg.get('show_player_command'):
                myscr.clear()
                myscr.addstr(0,0,cmdStr)
                #if mycfg.get('use_nexdef') and streamtype != 'audio':
                #   pos=6
                #else:
                #   pos=14
                #myscr.hline(pos,0,curses.ACS_HLINE, curses.COLS-1)
                #myscr.addstr(pos+1,0,'')
                myscr.refresh()
                time.sleep(1)

            play = MLBprocess(cmdStr)
            play.open()
            play.waitInteractive(myscr)


        # TODO: Needs attention for calendar
        if c in mykeys.get('INNINGS'):
            if mycfg.get('milbtv'):
                mywin.statusWrite('Jump to inning not supported for MiLB.',wait=2)
                continue
            if len(mywin.records) == 0:
                continue
            elif mywin==calwin and len(calwin.gamedata)==0:
                continue
            if mywin in ( optwin, helpwin, stdwin ):
                continue
            if mywin==calwin:
                prefer = calwin.alignCursors(mysched,listwin)
            if mycfg.get('use_nexdef') or \
               listwin.records[listwin.current_cursor][5] in ('F', 'CG')  or \
               listwin.records[listwin.current_cursor][7] == 'media_archive':
                pass
            else:
                error_str = 'ERROR: Jump to innings only supported for NexDef mode and archived games.'
                listwin.statusWrite(error_str,wait=2)
                continue

            innwin = MLBInningWin(myscr, mycfg, 
                                  listwin.records[listwin.current_cursor],
                                  mysched)
            innwin.Refresh()
            innwin.titleRefresh()
            try:
                start_time = innwin.selectToPlay()
            except:
                raise
            if start_time is not None:
                if prefer['video'] is None:
                    mywin.errorScreen('ERROR: Requested media not available.')
                    continue
                mediaStream = MediaStream(prefer['video'],
                                          session,mycfg,
                                          coverage=prefer['video'][1],
                                          streamtype='video',
                                          start_time=start_time)
                try:
                    mediaUrl = mediaStream.locateMedia()
                except:
                    mywin.errorScreen('ERROR: %s'%\
                                      mediaStream.error_str)
                    continue
                try:
                    mediaUrl = mediaStream.prepareMediaStreamer(mediaUrl)
                except:
                    mywin.errorScreen('ERROR: %s'%\
                                      mediaStream.error_str)
                    continue
                cmdStr = mediaStream.preparePlayerCmd(mediaUrl,
                                     listwin.records[listwin.current_cursor][6])
                play = MLBprocess(cmdStr)
                play.open()
                play.waitInteractive(myscr)
                
        if c in mykeys.get('LISTINGS') or c in mykeys.get('REFRESH') or \
           c in mykeys.get('MILBTV'):
            if mywin == calwin:
                try:
                    prefer = calwin.alignCursors(mysched,listwin)
                except:
                    prefer = dict()
                    prefer['audio'] = None
                    prefer['video'] = None
            mywin = listwin
            # refresh
            mywin.statusWrite('Refreshing listings...',wait=1)

            if c in mykeys.get('MILBTV'):
                # only need to reset listings to top first time
                # else, remember our place
                if not mycfg.get('milbtv'):
                    listwin.PgUp()
                mycfg.set('milbtv', True)
                try:
                    milbsession
                except:
                    mywin.statusWrite('Logging into milb.com...',wait=0)
                    milb_user=(mycfg.get('user') ,\
                        mycfg.get('milb_user'))[mycfg.data.has_key('milb_user')]
                    milb_pass=(mycfg.get('pass') ,\
                        mycfg.get('milb_pass'))[mycfg.data.has_key('milb_pass')]
                    milbsession = MiLBSession(user=milb_user,
                                              passwd=milb_pass,
                                              debug=mycfg.get('debug'))
                    try:
                        milbsession.getSessionData()
                    except MLBAuthError:
                        error_str = 'Login was unsuccessful.  Check user and pass in ' + myconf
                        mywin.statusWrite(error_str,wait=2)
                    except Exception,detail:
                        error_str = str(detail)
                        mywin.statusWrite(error_str,wait=2)
                    # align with mlbsched listings
                    (y,m,d) = (mlbsched.year,mlbsched.month,mlbsched.day)
                    try:
                        milbsched.Jump((y,m,d),mycfg.get('speed'), mycfg.get('blackout'))
                    except:
                        mywin.statusWrite(milbsched.error_str,wait=2)
                        mycfg.set('milbtv', False)
                        continue
                mysched = milbsched
            elif c in mykeys.get('LISTINGS'):
                if mycfg.get('milbtv'):
                    mycfg.set('milbtv', False)
                    listwin.PgUp()
                    if sbwin is not None:
                        sbwin.PgUp()
                mysched = mlbsched
            try:
                available = mysched.getListings(mycfg.get('speed'),
                                                mycfg.get('blackout'))
            except Exception,detail:
                mywin.statusWrite('ERROR: %s'%detail,wait=2)
                mywin.data = []
                mywin.records = []
                #pass
            else:
                mywin.data = available
                mywin.records = available[mywin.record_cursor:mywin.record_cursor+curses.LINES-4]
                listwin.focusFavorite()

        # TOGGLES
        if c in mykeys.get('DIVISION'):
            val=(True,False)[mycfg.get('highlight_division')]
            mycfg.set('highlight_division',val)

        if c in mykeys.get('NEXDEF'):
            if mywin not in ( listwin, sbwin, detailwin ):
                continue
            if mycfg.get('milbtv'):
                continue
            # there's got to be an easier way to do this
            if mycfg.get('use_nexdef'):
                mycfg.set('use_nexdef', False)
            else:
                mycfg.set('use_nexdef', True)

        if c in mykeys.get('COVERAGE'):
            if mywin not in ( listwin, sbwin, detailwin ):
                continue
            if mycfg.get('milbtv'):
                continue
            # there's got to be an easier way to do this
            temp = COVERAGETOGGLE.copy()
            del temp[mycfg.get('coverage')]
            for coverage in temp:
                mycfg.set('coverage', coverage)
            del temp

        if c in mykeys.get('SPEED'):
            if mywin not in ( listwin, sbwin, detailwin ):
                continue
            if mycfg.get('milbtv'):
                continue
            # there's got to be an easier way to do this
            if mycfg.get('use_nexdef'):
                if mycfg.get('adaptive_stream'):
                    mycfg.set('adaptive_stream', False)
                else:
                    mycfg.set('adaptive_stream', True)
                continue
            speeds = map(int, SPEEDTOGGLE.keys())
            speeds.sort()
            newspeed = (speeds.index(int(mycfg.get('speed')))+1) % len(speeds)
            mycfg.set('speed', str(speeds[newspeed]))

        if c in mykeys.get('DEBUG'):
            if mycfg.get('debug'):
                mycfg.set('debug', False)
            else:
                mycfg.set('debug', True)

        # ACTIONS
        # Override of Enter for RSS
        if c in ( 'Enter', 10 ):
            # implicit else allows Big Daddy Action to use Enter for video
            if mywin == rsswin:
                url = rsswin.data[(rsswin.current_cursor+rsswin.record_cursor)/2][1]
                browser = mycfg.get('rss_browser')
                try:
                    cmdStr = browser.replace('%s',"'" + url + "'")
                except:
                    cmdStr = browser + " '" + url + "'"
                proc = MLBprocess(cmdStr,retries=0)
                proc.open()
                proc.wait()
                continue
            elif mywin == boxwin:
                player=mywin.records[mywin.current_cursor][2]
                if player is None:
                    continue
                (id,flag,name) = player
                if flag:
                    type='batting'
                else:
                    type='pitching'
                # almost there... 
                # TODO: add in stats code including flags for url
                if mycfg.get('milbtv'):
                    mywin.statusWrite("Stats are not supported for MiLB",wait=2)
                    continue
                status_str="Retrieving %s stats for %s (%s)..." %\
                               ( type, name, id )
                mywin.statusWrite(status_str)
                mycfg.set('league','MLB')
                if type == 'pitching':
                    mycfg.set('stat_type','pitching')
                    mycfg.set('sort_column','era')
                else:
                    mycfg.set('stat_type','hitting')
                    mycfg.set('sort_column','avg')
                mycfg.set('player_id',0)
                mycfg.set('sort_team',0)
                mycfg.set('active_sw',0)
                mycfg.set('season_type','ANY')
                mycfg.set('sort_order',0)
                if int(id) > 1000:
                    mycfg.set('player_id',id)
                    mycfg.set('player_name',name)
                else:
                    mycfg.set('sort_team',id)
                    mycfg.set('season',datetime.datetime.now().year)
                mycfg.set('triple_crown', 0)
                try:
                    stats.getStatsData()
                except MLBUrlError:
                    raise
                statwin = MLBStatsWin(myscr,mycfg,stats.data,stats.last_update)
                mywin = statwin
                continue
            elif mywin == statwin:
                mywin = boxwin
                mywin.PgUp()
                continue
                

        # The Big Daddy Action  
        # With luck, it can handle audio, video, condensed, and highlights
        if c in mykeys.get('VIDEO') or \
           c in mykeys.get('AUDIO') or \
           c in mykeys.get('ALT_AUDIO') or \
           c in mykeys.get('CONDENSED_GAME'):
            if len(mywin.records) == 0:
                continue
            elif mywin == calwin and len(calwin.gamedata)==0:
                continue
            if mywin in ( optwin , helpwin, stdwin, statwin, boxwin ):
                continue
            if mywin in ( calwin, ):
                prefer = dict()
                prefer = calwin.alignCursors(mysched,listwin)
                if prefer == {}:
                    mywin.statusWrite('Could not get preferred media for %s' %\
                                       GAMEID,wait=2)
                    continue
            if c in mykeys.get('AUDIO') or c in mykeys.get('ALT_AUDIO'):
                if mywin == topwin:
                    listwin.statusWrite(UNSUPPORTED,wait=2)
                    continue
                if c in mykeys.get('ALT_AUDIO'):
                    streamtype = 'alt_audio'
                else:
                    streamtype = 'audio'
            elif c in mykeys.get('CONDENSED_GAME'):
                streamtype = 'condensed'
                try:
                    prefer[streamtype] = listwin.records[listwin.current_cursor][4][0]
                except:
                    mywin.errorScreen('ERROR: Requested media not available.')
                    continue
            else:
                streamtype = 'video'
            mywin.statusWrite('Retrieving requested media...')

            # for nexdef, use the innings list to find the correct start time
            if mycfg.get('use_nexdef') and not mycfg.get('milbtv'):
                start_time = mlbsched.getStartOfGame(listwin.records[listwin.current_cursor],mycfg)
            else:
                start_time = 0
            if prefer[streamtype] is None:
                mywin.errorScreen('ERROR: Requested media not available.')
                continue
            if mycfg.get('milbtv'):
                mediaStream = MiLBMediaStream(prefer[streamtype], milbsession, 
                                      mycfg,
                                      prefer[streamtype][1], 
                                      streamtype=streamtype,
                                      start_time=start_time)
            else:
                mediaStream = MediaStream(prefer[streamtype], session, mycfg,
                                      prefer[streamtype][1], 
                                      streamtype=streamtype,
                                      start_time=start_time)
            myscr.clear()
            myscr.addstr(0,0,'Requesting media: %s'% repr(prefer[streamtype]))
            myscr.refresh()
            if mywin == topwin:
                # top plays are handled just a bit differently from video
                streamtype = 'highlight'
                mediaUrl = topwin.records[topwin.current_cursor][2]
                eventId  = topwin.records[topwin.current_cursor][4]
            else:
                try:
                    mediaUrl = mediaStream.locateMedia()
                    mediaUrl = mediaStream.prepareMediaStreamer(mediaUrl)
                except Exception,detail:
                    if mycfg.get('debug'):
                        raise
                    myscr.clear()
                    myscr.addstr(0,0,'ERROR: %s' % str(detail))
                    myscr.addstr(3,0,'See %s for more details.'%LOGFILE)
                    myscr.refresh()
                    mywin.statusWrite('Press any key to continue',wait=-1)
                    continue
                # DONE: using direct address into listwin.records
                eventId  = listwin.records[listwin.current_cursor][6]

            cmdStr = mediaStream.preparePlayerCmd(mediaUrl, eventId,streamtype)
            if mycfg.get('show_player_command'):
                myscr.clear()
                chars=(curses.COLS-2) * (curses.LINES-1)
                myscr.addstr(0,0,cmdStr[:chars])
                #if mycfg.get('use_nexdef') and streamtype != 'audio':
                #   pos=6
                #else:
                #   pos=14
                #if pos < curses.LINES-4:
                #    myscr.hline(pos,0,curses.ACS_HLINE, curses.COLS-1)
                #    myscr.addstr(pos+1,0,'')
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
            # END OF Big Daddy Action
        
        if c in mykeys.get('RELOAD_CONFIG'):
            # reload the configuration
            mycfg = MLBConfig(mydefaults)
            mycfg.loads(myconf)
            # recreate the options window to reflect any changes
            optwin = MLBOptWin(myscr,mycfg)
            status_str = "Reloading " + str(myconf) + "..."
            mywin.statusWrite(status_str,wait=2)

            # Defensive code to insure speed is set correctly
            if not SPEEDTOGGLE.has_key(mycfg.get('speed')):
                s = 'Invalid speed in ' + str(myconf) +'.  Using speed=1200'
                mycfg.set('speed', '1200')
                mywin.statusWrite(s,wait=2)

            try:
                available = mlbsched.getListings(mycfg.get('speed'),
                                                mycfg.get('blackout'))
            except (KeyError,MLBXmlError),detail:
                if mycfg.get('debug'):
                    raise Exception,detail
                available = []
                status_str = "There was a parser problem with the listings page"
                mywin.statusWrite(status_str,wait=2)
            mywin.records = available[mywin.record_cursor:mywin.record_cursor+curses.LINES-4]

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
                  'alt_audio_follow': [],
                  'video_follow': [],
                  'blackout': [],
                  'favorite': [],
                  'use_color': 1,
                  'favorite_color': 'cyan',
                  'free_color': 'green',
                  'division_color' : 'red',
                  'highlight_division' : 0,
                  'bg_color': 'xterm',
                  'show_player_command': 0,
                  'debug': 0,
                  'curses_debug': 0,
                  'wiggle_timer': 0.5,
                  'x_display': '',
                  'top_plays_player': '',
                  'max_bps': 2400,
                  'min_bps': 1200,
                  'live_from_start': 0,
                  'use_nexdef': 0,
                  'use_wired_web': 1,
                  'adaptive_stream': 0,
                  'coverage' : 'home',
                  'show_inning_frames': 1,
                  'use_librtmp': 0,
                  'no_lirc': 0,
                  'postseason': 0,
                  'milbtv' : 0,
                  'rss_browser': 'firefox -new-tab %s',
                  'flash_browser': DEFAULT_FLASH_BROWSER}
    
    mycfg = MLBConfig(mydefaults)
    try:
        os.lstat(myconf)
    except:
        try:
            os.lstat(myconfdir)
        except:
            dir=myconfdir
        else:
            dir=None
        #doinstall(myconf,mydefaults,dir)
        mycfg.new(myconf, mydefaults, dir)

    #mycfg = MLBConfig(mydefaults)
    mycfg.loads(myconf)

    # DEFAULT_KEYBINDINGS is a dict() of default keybindings
    # found in MLBviewer/mlbDefaultKeyBindings.py rather than
    # MLBviewer/mlbConstants.py
    mykeyfile = os.path.join(myconfdir,'keybindings')
    mykeys = MLBKeyBindings(DEFAULT_KEYBINDINGS)
    mykeys.loads(mykeyfile)

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
        now=datetime.datetime.now()
        shift=mycfg.get('time_offset')
        gametime=MLBGameTime(now,shift=shift)

        if shift is not None and shift != '':
            offset=gametime.customoffset(time_shift=shift)
            now = now - offset
        else:
            tt=time.localtime()
            localzone=(time.timezone,time.altzone)[tt.tm_isdst]
            localoffset=datetime.timedelta(0,localzone)
            easternoffset=gametime.utcoffset()
            offset=localoffset - easternoffset
            now = now + offset
        #print "now = %s" % repr(now)
        # morning people may want yesterday's highlights, boxes, lines, etc
        # before day games begin.
        if now.hour < 9:
            dif = datetime.timedelta(days=1)
            now = now - dif
        startdate = (now.year, now.month, now.day)
        #raise Exception,"now.day= %s, offset= %s" % ( now.day, repr(offset) )

    curses.wrapper(mainloop, mycfg, mykeys)
