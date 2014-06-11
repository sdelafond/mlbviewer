#!/usr/bin/env

from mlbConstants import *
from mlbListWin import MLBListWin
from mlbCalendar import MLBCalendar
from mlbError import *
from mlbSchedule import gameTimeConvert
import datetime
import time
import calendar
import curses

def gametimeConvert(time_utc_str):
    utctime=time.strptime(time_utc_str,"%Y-%m-%dT%H:%M:%SZ")
    utcdate=datetime.datetime.fromtimestamp(time.mktime(utctime))
    localzone=(time.timezone,time.altzone)[time.daylight]
    localoffset= datetime.timedelta(0,localzone)
    localtime=utcdate-localoffset
    return localtime

class MLBCalendarWin(MLBListWin):

    def __init__(self,myscr,mycfg):
        self.myscr = myscr
        self.mycfg = mycfg
        # any gid will do
        # DONE: Leave it as gid ; necessary to align with listings view
        #( self.year, self.month, self.day ) = mysched.data[0][1]
        self.statuswin = curses.newwin(1,curses.COLS-1,curses.LINES-1,0)
        self.titlewin = curses.newwin(2,curses.COLS-1,0,0)
        self.data = []
        self.records = []
        self.current_cursor = 0
        self.record_cursor = 0
        self.game_cursor = 0
        self.calendar = MLBCalendar()

    def alignCursors(self,mysched,listwin):
        prefer = dict()
        if len(self.gamedata) > 0:
            ( gameid, isaway ) = self.gamedata[self.game_cursor][:2]
        else:
            return prefer
        coverage = ('home','away')[isaway]
        self.mycfg.set('coverage', coverage)
        ( year, month, day ) = gameid.split('/')[:3]
        ymd_tuple = ( int(year), int(month), int(day) )
        listwin.data = mysched.Jump(ymd_tuple,
                                     self.mycfg.get('speed'),
                                     self.mycfg.get('blackout'))
        listwin.records = listwin.data[:curses.LINES-4]
        listwin.current_cursor = 0
        listwin.record_cursor = 0
        for game in listwin.data:
            if game[6] != gameid:
                listwin.Down()
            else:
                prefer = mysched.getPreferred(game,self.mycfg)
                break
        return prefer
        
    def Jump(self,ymd_tuple):
        (year,month,day) = ymd_tuple
        self.year = int(year)
        self.month = int(month)
        self.getData(self.team,self.year,self.month)

    def getData(self,team,year=None,month=None):
        self.data = []
        self.team = team
        if year is not None and month is not None:
            self.year = year
            self.month = month
        else:
            now = datetime.datetime.now()
            self.year = now.year
            self.month = now.month
        try:
            self.cal = self.calendar.getData(self.team,self.year,self.month)
        except:
            raise
            self.error_str = "UrlError: Could not retrieve calendar."
            raise MLBUrlError
        self.days = self.calendar.calendarMonth()
        self.buildCalendarData()
        # this is all just initialization ; setCursors should be called to
        # align with listings position
        self.game_cursor = 0
        self.current_cursor = 0
        self.record_cursor = 0
        viewable=(curses.LINES-4)/4
        self.records = self.data[:viewable]       


    def buildCalendarData(self):
        # Different than other windows, the cursor is a game cursor rather
        # than a line cursor.  Other commands from the calendar screen such
        # as AUDIO/VIDEO/CONDENSED/BOX/LINE, etc will be based from 
        # self.gamedata[self.game_cursor] rather than self.data or self.records.
        self.gamedata = []
        # self.data is just for building the GUI lines.
        self.data = []
        weekdays = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
        weekday=0
        # e.g. SUN 30
        line1=''
        # e.g. @DET
        line2=''
        # first game score or schedule
        line3=''
        # second game score or schedule (if doubleheader)
        line4=''
        for game in self.days:
            # line1=....
            gamedate=game[0]
            dayofweek=weekdays[(gamedate.weekday()+1)%7]
            line1+="%3s %02d%3s" % ( dayofweek, gamedate.day, ' '*3 )
            # line2=....
            if game[1] is not None:
                try:
                    ( isAway, this, that ) = self.parseTeams(game[1][0])
                    opponent = int(that['id'])
                except:
                    line2+=' '*9
                else:
                    opponent = int(that['id'])
                    line2+='%s%-3s%5s' % ( (' ', '@')[isAway],
                                      STATS_TEAMS[opponent].upper(), ' '*5 )
            else:
                line2+=' '*9
            # line3=....
            if game[1] is None:
                line3+=' '*9
            else:
                try:
                    ( isAway, this, that ) = self.parseTeams(game[1][0])
                    opponent = int(that['id'])
                except:
                    line3=' '*9
                else:
                    line3+=self.parseScheduleResult(game[1][0],this,that)
                    self.gamedata.append((game[1][0]['game_id'], isAway, game[1][0]))
            # line4=....
            if game[1] is not None and len(game[1]) == 2:
                try:
                    ( isAway, this, that ) = self.parseTeams(game[1][1])
                    opponent = int(that['id'])
                except:
                    line4=' '*9
                else:
                    line4+=self.parseScheduleResult(game[1][1],this,that)
                    self.gamedata.append((game[1][1]['game_id'], isAway, game[1][1]))
            else:
                line4+=' '*9
            # Whew!  Made it through another week.  Pack it up and get ready
            # for the next week.
            if dayofweek == 'SAT':
                self.data.append((line1, line2, line3, line4))
                line1=''
                line2=''
                line3=''
                line4=''
        # Add any remaining partial week.
        if line1 != '':
            self.data.append((line1, line2, line3, line4))

    def parseTeams(self,game):
        teams = (int(game['home']['id']),
                 int(game['away']['id']))
        try:
            # isAway will be used in calendar but also for coverage in 
            # playing media.
            # This doesn't handle ASG.
            isAway =  teams.index(self.team)
        except:
            raise Exception,repr(game)
        opponent = ( teams[1], teams[0] )[isAway]
        # "this" is the calendar team, "that" is the opponent
        this =  ( game['home'], game['away'] )[isAway]
        that =  ( game['home'], game['away'] )[not isAway]
        return ( isAway, this, that )

    def parseScheduleResult(self,game,this,that):
        out=''
        if game is None:
            return ' '*9
        status = game['game_status']
        if status in ( 'F', 'I', 'O' ):
            thisRuns=int(this['runs'])
            thatRuns=int(that['runs'])
            if status in ( 'F', 'O' ):
                result = ( 'L', 'W' )[(thisRuns > thatRuns)]
            else:
                result = ""
            result += ' ' + str(thisRuns) + '-' + str(thatRuns)
        elif status in ( 'S', ):
            if game['time_is_tbd']:
                result="TBD"
            else:
                localtime=gametimeConvert(game['time_utc'])
                (hour,min) = (localtime.hour, localtime.minute)
                ampm = 'AM'
                if localtime.hour > 12:
                    hour-=12
                    ampm='PM'
                result = "%2d:%02d%s" % ( hour, min, ampm )
                #result=(game['time_local'][-11:])[:5]
                
        elif status in ( 'D', ):
            result="PPD"
        elif status in ( 'C', ):
            result="CANCEL"
        else:
            result="unkSts:%s" % status
        out+= "%-9s" % result
        return out

    # TODO: Up/Down will scroll through the days and Left/Right forward and 
    # back a month
    def Up(self):
        if self.game_cursor - 1 >= 0:
            self.game_cursor -= 1

    def Down(self):
        if self.game_cursor + 1 < len(self.gamedata):
            self.game_cursor += 1
        # Silent else do nothing at bottom of window and bottom of records

    def Left(self):
        # Months are front-filled no more than 6 days, so a delta of 10
        # should be sufficient to get into the prior month.
        thisDate=self.days[0][0]
        dif=datetime.timedelta(days=10)
        newDate=thisDate-dif
        ( self.year , self.month ) = ( newDate.year , newDate.month )
        self.getData(self.team, self.year, self.month )

    def Right(self):
        # Months are not back-filled with any extra days.  Delta of 1 day
        # should be sufficient to get the next month.
        thisDate=self.days[-1][0]
        dif=datetime.timedelta(days=1)
        newDate=thisDate+dif
        ( self.year , self.month ) = ( newDate.year , newDate.month )
        self.getData(self.team, self.year, self.month )

    def Refresh(self):

        self.myscr.clear()
        # display even number of lines since days will be four lines
        wlen = curses.LINES-4
        if wlen % 4 > 0:
            wlen -= wlen % 4
        if len(self.days) == 0:
            self.myscr.refresh()
            return
        y=2
        for n in range(len(self.records)):
            if n < len(self.records):
                for line in self.records[n]:
                    self.myscr.addstr(y,0,line)
                    y+=1        
            else:
                s = ' '*(curses.COLS-1)
                self.myscr.addnstr(n+2,0,s,curses.COLS-2)
        # To handle the cursor, scroll through the games only.
        # However, the display is drawn from days.  So find the day from 
        # the game id and determine how many days from the start of the 
        # calendar.
        if len(self.gamedata) == 0:
            self.myscr.refresh()
            return
        game_id=self.gamedata[self.game_cursor][0]
        ( year, month, day ) = game_id.split('/')[:3]
        gameday = datetime.datetime(int(year),int(month),int(day))
        dayzero = self.days[0][0]
        day_dif = gameday - dayzero
        day_cursor = day_dif.days
        # find the week from the day cursor
        week=(day_cursor)/7
        day=(day_cursor%7)+1
        ypos=(week*4)+4
        # This does not handle Spring Training split squad games.  Sorry.
        if game_id.split('-')[-1] == '2':
            ypos+=1
        xpos=(day-1)*9
        try:
            self.myscr.chgat(ypos,xpos,7,curses.A_REVERSE)
        except:
            raise MLBCursesError,"Terminal does not have enough lines to display this screen."
            raise Exception,"gc=%s,y=%s,x=%s"%(self.game_cursor,ypos,xpos)
        
        self.myscr.refresh()
        if self.mycfg.get('curses_debug'):
            # This is pretty much just for me.  If you need to debug
            # the cursor code, you can put your own variable string here.
            s="gc=%s,dc=%s,y=%s,x=%s,lgd=%s,gid=%s" % (self.game_cursor,day_cursor,ypos,xpos,len(self.gamedata),game_id)
            self.statuswin.addnstr(0,0,s,curses.COLS-2,curses.A_BOLD)
            self.statuswin.refresh()
                
    def titleRefresh(self,mysched):
        self.titlewin.clear()
        filecode=STATS_TEAMS[self.team]
        teamStr=TEAMCODES[filecode][1]
        titlestr = "CALENDAR FOR %3s (%s %s)" %\
                ( teamStr,
                calendar.month_name[self.month] , self.year )
                # DONE: '(Use arrow keys to change days)'

        padding = curses.COLS - (len(titlestr) + 6)
        titlestr += ' '*padding
        pos = curses.COLS - 6
        self.titlewin.addstr(0,0,titlestr)
        self.titlewin.addstr(0,pos,'H', curses.A_BOLD)
        self.titlewin.addstr(0,pos+1, 'elp')
        self.titlewin.hline(1, 0, curses.ACS_HLINE, curses.COLS-1)
        self.titlewin.refresh()

    def statusRefresh(self):
        if len(self.days) == 0:
            self.statuswin.addnstr(0,0,'No calendar available for this month.',
                                       curses.COLS-2)
            self.statuswin.refresh()
            return
        if self.mycfg.get('curses_debug'):
            # Let Refresh() handle curses_debug so we don't have to repeat
            # the calculations here.
            return
        else:
            s = "Up/Down: Change games | Left/Right: Change months | C: Change team"
        padding=(curses.COLS-2)-len(s)
        status_str = s + ' '*padding
        self.statuswin.addnstr(0,0,status_str,curses.COLS-2,curses.A_BOLD)
        self.statuswin.refresh()

    def getTeamFromUser(self):
        team = self.prompter(self.statuswin,'Enter teamcode for calendar:')
        team = team.strip()
        if team not in TEAMCODES.keys():
            self.statusWrite('Invalid teamcode: '+team,wait=2)
            return
        else:
            return team
