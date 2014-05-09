#!/usr/bin/env

from mlbConstants import *
from mlbListWin import MLBListWin
from mlbMasterScoreboard import MLBMasterScoreboard
from mlbError import *
from mlbSchedule import gameTimeConvert
import datetime
import curses

class MLBMediaDetailWin(MLBListWin):

    def __init__(self,myscr,mycfg,gid,games):
        self.myscr = myscr
        self.mycfg = mycfg
        # any gid will do
        # DONE: Leave it as gid ; necessary to align with listings view
        #( self.year, self.month, self.day ) = mysched.data[0][1]
        self.gid = gid
        self.gameid = gid
        self.gameid = self.gameid.replace('/','_')
        self.gameid = self.gameid.replace('-','_')
        ( self.year, self.month, self.day ) = self.gameid.split('_')[:3]
        self.games = games
        self.statuswin = curses.newwin(1,curses.COLS-1,curses.LINES-1,0)
        self.titlewin = curses.newwin(2,curses.COLS-1,0,0)
        self.data = []
        self.records = []
        self.current_cursor = 0
        self.record_cursor = 0
        self.game_cursor = 0


    def getMediaDetail(self,gid):
        self.gid = gid
        self.data = []
        self.records = []

        # This method does parsing and formatting of media detail for Refresh
        self.formatMediaDetail()

        # This is all just initialization ; setCursors should be called to
        # align with listings position
        self.game_cursor = 0
        self.current_cursor = 0
        self.record_cursor = 0
        viewable = curses.LINES-4
        if viewable % 2 > 0:
            viewable -= 1
        self.records = self.data[:viewable]

    def setCursors(self,current_cursor,record_cursor):
        self.game_cursor = current_cursor + record_cursor
        # scoreboard scrolls two lines at a time
        absolute_cursor = self.game_cursor * 2
        viewable = curses.LINES-4
        if viewable % 2 > 0:
            viewable -= 1
        # integer division will give us the correct top record position
        try:
            self.record_cursor = ( absolute_cursor / viewable ) * viewable
        except:
            raise MLBCursesError,"Screen too small."
        # and find the current position in the viewable screen
        self.current_cursor = absolute_cursor - self.record_cursor
        # and finally collect the viewable records
        self.records = self.data[self.record_cursor:self.record_cursor+viewable]

    def formatMediaDetail(self):
        for game in self.games:
            status = game['status']
            start = game['starttime']
            starttime = start.strftime('%I:%M %p')
            away_video=game['media']['video']['away']
            home_video=game['media']['video']['home']
            away_audio=game['media']['audio']['away']
            home_audio=game['media']['audio']['home']
            away_vidstr = ("(No Video)",away_video[0])[len(away_video)>0]
            home_vidstr = ("(No Video)",home_video[0])[len(home_video)>0]
            away_audstr = ("(No Audio)",away_audio[0])[len(away_audio)>0]
            home_audstr = ("(No Audio)",home_audio[0])[len(home_audio)>0]
            cg_str = ("[-]","[C]")[len(game['media']['condensed'])>0]
            archive_str = ("[-]", "[A]")[game['archive']]
            mediaflags = "%s%s" % ( cg_str, archive_str )
            away_substr1 = "%3s | [Video] %s" % \
                ( game['away'].upper(), away_vidstr )
            away_substr2 = "%3s | [Audio] %s" % \
                ( "", away_audstr )
            #away_str = "%10s%25s%25s%10s" % ( status, away_substr1, away_substr2, mediaflags )
            away_str = "%10s   %-25s %-25s   %7s" % ( status, away_substr1, away_substr2, mediaflags )
            home_substr1 = "%3s | [Video] %s" % \
                ( game['home'].upper(), home_vidstr )
            home_substr2 = "%3s | [Audio] %s" % \
                ( "", home_audstr )
            #home_str = "%10s%25s%25s" % ( starttime, home_substr1, home_substr2 )
            home_str = "%10s   %-25s %-25s" % ( starttime, home_substr1, home_substr2 )
            self.data.append(away_str)
            self.data.append(home_str)
        return self.data

    def Up(self):
        if self.current_cursor - 2 < 0 and self.record_cursor - 2 >= 0:
            viewable = curses.LINES-4
            if viewable % 2 > 0:
                viewable -= 1
            self.current_cursor = viewable-2
            #if self.current_cursor % 2 > 0:
            #    self.current_cursor -= 1
            if self.record_cursor - viewable < 0:
                self.record_cursor = 0
            else:
                self.record_cursor -= viewable
                #if self.record_cursor % 2 > 0:
                #    self.record_cursor -= 1
            self.records = self.data[self.record_cursor:self.record_cursor+viewable]
        elif self.current_cursor > 0:
            self.current_cursor -= 2

    def Down(self):
        viewable=curses.LINES-4
        if self.current_cursor + 2 >= len(self.records) and\
           ( self.record_cursor + self.current_cursor + 2 ) < len(self.data):
            self.record_cursor += self.current_cursor + 2
            self.current_cursor = 0
            if ( self.record_cursor + viewable ) % 2 > 0:
                self.records = self.data[self.record_cursor:self.record_cursor+curses.LINES-5]
            else:
                self.records = self.data[self.record_cursor:self.record_cursor+curses.LINES-4]
        # Elif not at bottom of window
        elif self.current_cursor + 2 < self.records  and\
             self.current_cursor + 2  < curses.LINES-4:
            if (self.current_cursor + 2 + self.record_cursor) < len(self.data):
                self.current_cursor += 2
        # Silent else do nothing at bottom of window and bottom of records


    def Refresh(self):

        self.myscr.clear()
        # display even number of lines since games will be two lines
        wlen = curses.LINES-4
        if wlen % 2 > 0:
            wlen -= 1
        if len(self.games) == 0:
            self.myscr.refresh()
            return
        for n in range(wlen):
            if n < len(self.records):
                s = self.records[n]
                cursesflags = 0
                game_cursor = ( n + self.record_cursor ) / 2
                home = self.games[game_cursor]['home']
                away = self.games[game_cursor]['away']
                status = self.games[game_cursor]['statustext']
                if n % 2 > 0:
                    # second line of the game, underline it for division
                    # between games
                    pad = curses.COLS -1 - len(s)
                    s += ' '*pad
                    if n - 1 == self.current_cursor:
                        cursesflags |= curses.A_UNDERLINE|curses.A_REVERSE
                    else:
                        cursesflags = curses.A_UNDERLINE
                    if status in ( 'In Progress', 'Replay' ):
                        cursesflags |= cursesflags | curses.A_BOLD
                else:
                    pad = curses.COLS -1 - len(s)
                    s += ' '*pad
                    if n == self.current_cursor:
                        cursesflags |= curses.A_REVERSE
                    else:
                        cursesflags = 0
                    if status in ( 'In Progress', 'Replay' ):
                        cursesflags |= cursesflags | curses.A_BOLD
                if home in self.mycfg.get('favorite') or \
                   away in self.mycfg.get('favorite'):
                    if self.mycfg.get('use_color'):
                        cursesflags |= curses.color_pair(1)
                self.myscr.addnstr(n+2,0,s,curses.COLS-2,cursesflags)
            else:
                s = ' '*(curses.COLS-1)
                self.myscr.addnstr(n+2,0,s,curses.COLS-2)
        self.myscr.refresh()
                
    def titleRefresh(self,mysched):
        self.titlewin.clear()
        titlestr = "MEDIA DETAIL VIEW FOR " +\
                str(mysched.month) + '/' +\
                str(mysched.day) + '/' +\
                str(mysched.year)
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
        if len(self.games) == 0:
            self.statuswin.addnstr(0,0,'No listings available for this day.',
                                       curses.COLS-2)
            self.statuswin.refresh()
            return
        game_cursor = ( self.current_cursor + self.record_cursor ) / 2
        # BEGIN curses debug code
        if self.mycfg.get('curses_debug'):
            wlen=curses.LINES-4
            if wlen % 2 > 0:
                wlen -= 1
            status_str = "game_cursor=%s, wlen=%s, current_cursor=%s, record_cursor=%s, len(records)=%s" %\
                      ( game_cursor, wlen, self.current_cursor, self.record_cursor, len(self.records) )
            self.statuswin.clear()
            self.statuswin.addnstr(0,0,status_str,curses.COLS-2,curses.A_BOLD)
            self.statuswin.refresh()
            return
        # END curses debug code
        status = self.games[game_cursor]['statustext']
        status_str = status
        speedstr = SPEEDTOGGLE.get(self.mycfg.get('speed'))
        hdstr = SSTOGGLE.get(self.mycfg.get('adaptive_stream'))
        coveragestr = COVERAGETOGGLE.get(self.mycfg.get('coverage'))
        status_str_len = len(status_str) +\
                            + len(speedstr) + len(hdstr) + len(coveragestr) + 2
        if self.mycfg.get('debug'):
            status_str_len += len('[DEBUG]')
        padding = curses.COLS - status_str_len
        # shrink the status string to fit if it is too many chars wide for
        # screen
        if padding < 0:
            status_str=status_str[:padding]
        if self.mycfg.get('debug'):
            debug_str = '[DEBUG]'
        else:
            debug_str = ''
        if self.mycfg.get('use_nexdef'):
            speedstr = '[NEXDF]'
        else:
            hdstr = SSTOGGLE.get(False)
        status_str += ' '*padding + debug_str +  coveragestr + speedstr + hdstr

        self.statuswin.addnstr(0,0,status_str,curses.COLS-2,curses.A_BOLD)
        self.statuswin.refresh()
