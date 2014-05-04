#!/usr/bin/env python

import curses
import curses.textpad
import time
import os
#from listwin import ListWin
from mlbConstants import *
from mlbError import *

class MLBListWin:

    def __init__(self,myscr,mycfg,data):
        # self.data is everything
        self.data = data
        # self.records is only what's "visible"
        self.records = self.data[0:curses.LINES-4]
        self.mycfg = mycfg
        self.myscr = myscr
        self.current_cursor = 0
        self.record_cursor = 0
        self.statuswin = curses.newwin(1,curses.COLS-1,curses.LINES-1,0)
        self.titlewin = curses.newwin(2,curses.COLS-1,0,0)

    def getsize(self):
        ( y , x ) = os.popen('stty size', 'r').read().split()
        curses.LINES = int(y)
        curses.COLS = int(x) 
        return ( curses.LINES , curses.COLS )

    def resize(self):
        try:
            self.statuswin.clear()
            self.statuswin.mvwin(curses.LINES-1,0)
            self.statuswin.resize(1,curses.COLS-1)
            self.titlewin.mvwin(0,0)
            self.titlewin.resize(2,curses.COLS-1)
        except Exception,e:
            raise Exception,repr(e)
            raise Exception,"y , x = %s, %s" % ( curses.LINES-1 , 0 )
        viewable = curses.LINES-4
        # even out the viewable region if odd number of lines for scoreboard 
        if viewable % 2 > 0:
            viewable -= 1
        # adjust the cursors to adjust for viewable changing
        # 1. first figure out absolute cursor value
        absolute_cursor = self.record_cursor + self.current_cursor
        # 2. top of viewable is record_cursor, integer divison of viewable
        try:
            self.record_cursor = ( absolute_cursor / viewable ) * viewable
        except:
            raise MLBCursesError, "Screen too small."
        # 3. current position in viewable screen
        self.current_cursor = absolute_cursor - self.record_cursor
        # finally adjust the viewable region
        self.records = self.data[self.record_cursor:self.record_cursor+viewable]
        
    def prompter(self,win,prompt):
        win.clear()
        win.addstr(0,0,prompt,curses.A_BOLD)
        win.refresh()

        responsewin = win.derwin(0, len(prompt))
        responsebox = curses.textpad.Textbox(responsewin)
        responsebox.edit()
        output = responsebox.gather()
        return output

    def Splash(self):
        lines = ('mlbviewer', VERSION, URL)
        for i in xrange(len(lines)):
            self.myscr.addnstr(curses.LINES/2+i, (curses.COLS-len(lines[i]))/2,                                lines[i],curses.COLS-2)
        self.myscr.refresh()

    def Up(self):
        # Are we at the top of the window 
        # Do we have more records below record cursor?
        # Move up a window in the records.
        if self.current_cursor -1 < 0 and self.record_cursor - 1 >= 0:
            viewable= curses.LINES-4
            self.current_cursor = viewable - 1
            if self.record_cursor - viewable < 0:
                self.record_cursor = 0
            else:
                self.record_cursor -= viewable
            self.records = self.data[self.record_cursor:self.record_cursor+viewable]
            #raise Exception,repr(self.records)
        # Elif we are not yet at top of window
        elif self.current_cursor > 0:
            self.current_cursor -= 1
        # Silent else do nothing when at top of window and top of records
        # no negative scrolls

    def Down(self):
        # old behavior
        #if self.current_cursor + 1 < len(self.data):
        #    self.current_cursor += 1
        
        # Are we at bottom of window and
        # still have more records?
        # Move down a window.
        if self.current_cursor + 1 >= len(self.records) and\
          self.record_cursor + self.current_cursor + 1 < len(self.data):
           self.record_cursor += self.current_cursor + 1
           self.current_cursor = 0
           self.records = self.data[self.record_cursor:self.record_cursor+curses.LINES-4]
        # Elif not at bottom of window
        elif self.current_cursor + 1 < self.records  and\
            self.current_cursor + 1 < curses.LINES-4:
            if self.current_cursor + 1 + self.record_cursor < len(self.data):
                self.current_cursor += 1
        # Silent else do nothing at bottom of window and bottom of records


    def PgUp(self):
        self.current_cursor = 0
        self.record_cursor = 0
        viewlen = curses.LINES-4
        # tweak for scoreboard
        if viewlen % 2 > 0:
            viewlen -= 1
        self.records = self.data[:viewlen]

    def PgDown(self):
        # assuming we scrolled down, we'll have len(data) % ( curses.LINES-4 )
        # records left to display
        remaining=len(self.data) % ( curses.LINES-4 )
        self.records = self.data[-remaining:]
        self.record_cursor = len(self.data)- remaining
        self.current_cursor = len(self.records) - 1

    def focusFavorite(self):
        for n in range(len(self.data)):
            home = str(self.data[n][0]['home'])
            away = str(self.data[n][0]['away'])
            if home in self.mycfg.get('favorite') or \
               away in self.mycfg.get('favorite'):
                # Find the correct screen to focus on.
                # This is intended only on initial listing so record_cursor
                # is assumed to be zero (first screen.)  Check to see if we
                # need to scroll a screen.
                if n > (curses.LINES-4):
                    # Not on this screen. Check to see how many screens to 
                    # advance.
                    screens = n / (curses.LINES-4)
                    self.record_cursor = (curses.LINES-4) * screens
                    self.current_cursor = n % self.record_cursor
                    remaining=len(self.data) - self.record_cursor
                    if remaining > (curses.LINES-4):
                        remaining=(curses.LINES-4)+self.record_cursor + 1
                    else:
                        remaining+=self.record_cursor + 1
                    self.records=self.data[self.record_cursor:remaining]
                    return
                else:
                    self.current_cursor = n
                    return
            n+=1
                
    def Refresh(self):
        if len(self.data) == 0:
            #status_str = "There was a parser problem with the listings page"
            #self.statuswin.addstr(0,0,status_str)
            self.titlewin.refresh()
            self.myscr.refresh()
            self.statuswin.refresh()
            #time.sleep(2)
            return

        self.myscr.clear()
        for n in range(curses.LINES-4):
            if n < len(self.records):
                home = str(self.records[n][0]['home'])
                away = str(self.records[n][0]['away'])
                s = self.records[n][1].strftime('%l:%M %p') + ': ' +\
                    TEAMCODES[away][1] + ' at ' +\
                    TEAMCODES[home][1]
                #s = self.records[n][1].strftime('%l:%M %p') + ': ' +\
                #    ' '.join(TEAMCODES[away][1:]).strip() + ' at ' +\
                #    ' '.join(TEAMCODES[home][1:]).strip()
                if len(self.records[n]) > 8 and self.records[n][9]:
                    s += ' [FREE]'
                if self.records[n][7] == 'media_archive':
                    s += ' (Archived)'

                padding = curses.COLS - (len(s) + 1)
                if n == self.current_cursor:
                    s += ' '*padding
            else:
                s = ' '*(curses.COLS-1)

            if n == self.current_cursor:
                if self.records[n][5] == 'I':
                    # highlight and bold if in progress, else just highlight
                    cursesflags = curses.A_REVERSE|curses.A_BOLD
                else:
                    cursesflags = curses.A_REVERSE
            else:
                if n < len(self.records):
                    if self.records[n][5] == 'I':
                        cursesflags = curses.A_BOLD
                    else:
                        cursesflags = 0

            if n < len(self.records):
                if home in self.mycfg.get('favorite') or\
                   away in self.mycfg.get('favorite'):
                    if self.mycfg.get('use_color'):
                        cursesflags = cursesflags |curses.color_pair(COLOR_FAVORITE)
                    else:
                        cursesflags = cursesflags | curses.A_UNDERLINE
                elif len(self.records[n])> 8 and self.records[n][9]:
                    if self.mycfg.get('use_color'):
                        cursesflags = cursesflags | curses.color_pair(COLOR_FREE)
                    else:
                        cursesflags = cursesflags | curses.A_UNDERLINE
                self.myscr.addnstr(n+2, 0, s, curses.COLS-2, cursesflags)
                #if n == 0:
                #    self.myscr.addch(n+2, curses.COLS-2, curses.ACS_UARROW)
            else:
                self.myscr.addnstr(n+2, 0, s, curses.COLS-2)

        self.myscr.refresh()

    def titleRefresh(self,mysched):
        titlestr = "AVAILABLE GAMES FOR " +\
                str(mysched.month) + '/' +\
                str(mysched.day) + '/' +\
                str(mysched.year) + ' ' +\
                '(Use arrow keys to change days)'

        padding = curses.COLS - (len(titlestr) + 6)
        titlestr += ' '*padding
        pos = curses.COLS - 6
        self.titlewin.clear()
        self.titlewin.addstr(0,0,titlestr)
        self.titlewin.addstr(0,pos,'H', curses.A_BOLD)
        self.titlewin.addstr(0,pos+1, 'elp')
        self.titlewin.hline(1, 0, curses.ACS_HLINE, curses.COLS-1)
        self.titlewin.refresh()

    def statusRefresh(self):
        # BEGIN curses debug code
        game_cursor = ( self.current_cursor + self.record_cursor )
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
        n = self.current_cursor
        if len(self.records) == 0:
            status_str = "No listings available for this day."
            self.statuswin.clear()
            self.statuswin.addnstr(0,0,status_str,curses.COLS-2)
            self.statuswin.refresh()
            return

        try:
            status_str = STATUSLINE.get(self.records[n][5],
                                    "Unknown Flag = "+self.records[n][5])
        except:
            raise Exception,"current_cursor:%s, len:%s"%(n,str(len(self.records)))
        if len(self.records[n][2]) + len(self.records[n][3]) == 0:
            status_str += ' (No media)'
        elif len(self.records[n][2]) == 0:
            status_str += ' (No video)'
        elif len(self.records[n][3]) == 0:
            status_str += ' (No audio)'

        if self.mycfg.get('milbtv'):
            speedstr = "[1000K]"
            coveragestr="[MiLB]"
            hdstr=SSTOGGLE.get(False)
        else:
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
        if self.mycfg.get('use_nexdef') and not self.mycfg.get('milbtv'):
            speedstr = '[NEXDF]'
        else:
            hdstr = SSTOGGLE.get(False)

        status_str += ' '*padding + debug_str +  coveragestr + speedstr + hdstr
        # And write the status
        try:
            self.statuswin.addnstr(0,0,status_str,curses.COLS-2,curses.A_BOLD)
        except:
            rows = curses.LINES
            cols = curses.COLS
            slen = len(status_str)
            raise Exception,'(' + str(slen) + '/' + str(cols) + ',' + str(n) + '/' + str(rows) + ') ' + status_str
        self.statuswin.refresh()

    def helpScreen(self):
        self.myscr.clear()
        self.titlewin.clear()
        self.myscr.addstr(0,0,VERSION)
        self.myscr.addstr(0,20,URL)
        n = 1

        for heading in HELPFILE:
           if n < curses.LINES-4:
               self.myscr.addnstr(n,0,heading[0],curses.COLS-2,
                                                 curses.A_UNDERLINE)
           else:
               continue
           n += 1
           for helpkeys in heading[1:]:
               for k in helpkeys:
                   if n < curses.LINES-4:
                       helpstr = "%-20s: %s" % ( k , KEYBINDINGS[k] )
                       #self.myscr.addstr(n,0,k)
                       #self.myscr.addstr(n,20, ': ' + KEYBINDINGS[k])
                       self.myscr.addnstr(n,0,helpstr,curses.COLS-2)
                   else:
                       continue
                   n += 1
        self.statuswin.clear()
        self.statuswin.addnstr(0,0,'Press a key to continue...',curses.COLS-2)
        self.myscr.refresh()
        self.statuswin.refresh()
        self.myscr.getch()

    def errorScreen(self,errMsg):
        if self.mycfg.get('debug'):
            raise
        self.myscr.clear()
        self.myscr.addnstr(0,0,errMsg,curses.COLS-2)
        self.myscr.addnstr(2,0,'See %s for more details.'%LOGFILE,curses.COLS-2)
        self.myscr.refresh()
        self.statuswin.clear()
        self.statuswin.addnstr(0,0,'Press a key to continue...',curses.COLS-2)
        self.statuswin.refresh()
        self.myscr.getch()

    def statusWrite(self, statusMsg, wait=0):
        self.statuswin.clear()
        self.statuswin.addnstr(0,0,str(statusMsg),curses.COLS-2,curses.A_BOLD)
        self.statuswin.refresh()
        if wait < 0:
            self.myscr.getch()
        elif wait > 0:
            time.sleep(wait)
