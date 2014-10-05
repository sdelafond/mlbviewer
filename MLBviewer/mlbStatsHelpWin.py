#!/usr/bin/env python

import curses
import curses.textpad
import time
from mlbListWin import MLBListWin
from mlbConstants import *

class MLBStatsHelpWin(MLBListWin):

    def __init__(self,myscr,mykeys):
        self.mykeys = mykeys
        self.data = []
        for heading in STATHELPBINDINGS:
            self.data.append((heading[0],curses.A_UNDERLINE))
            for helpkeys in heading[1:]:
                for k in helpkeys:
                    keylist = self.mykeys.get(k)
                    if isinstance(keylist, list):
                        for elem in keylist:
                            # some keys don't translate well so macro will 
                            # convert it to something more meaningful if 
                            # possible
                            keystr = self.mykeys.macro(elem)
                            helpstr="%-20s: %s" % (keystr, STATKEYBINDINGS[k])
                            self.data.append((helpstr, 0))
                    else:
                        try:
                            keystr = self.mykeys.macro(keylist)
                        except:
                            #raise Exception,repr(keylist) + k
                            raise 
                        helpstr="%-20s: %s" % (keystr, STATKEYBINDINGS[k])
                        self.data.append((helpstr, 0))
        # data is everything, records is only what's visible
        self.records = self.data[0:curses.LINES-4]
        self.myscr = myscr
        self.current_cursor = 0
        self.record_cursor = 0
        self.statuswin = curses.newwin(1,curses.COLS-1,curses.LINES-1,0)
        self.titlewin = curses.newwin(2,curses.COLS-1,0,0)

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
                #s = "%s = %s" % (self.records[n][0], self.records[n][1])
                ( s, cflags ) = self.records[n]

                padding = curses.COLS - (len(s) + 1)
                if n == self.current_cursor:
                    s += ' '*padding
            else:
                s = ' '*(curses.COLS-1)

            if n == self.current_cursor:
                cursesflags = curses.A_REVERSE|curses.A_BOLD|cflags
            else:
                if n < len(self.records):
                    cursesflags = 0|cflags
            if n < len(self.records):
                self.myscr.addnstr(n+2, 0, s, curses.COLS-2, cursesflags)
            else:
                self.myscr.addnstr(n+2, 0, s, curses.COLS-2)

        self.myscr.refresh()

    def titleRefresh(self):
        titlestr = "%-20s%s" % ( VERSION, URL )

        padding = curses.COLS - len(titlestr) 
        titlestr += ' '*padding
        self.titlewin.addstr(0,0,titlestr)
        self.titlewin.hline(1, 0, curses.ACS_HLINE, curses.COLS-1)
        self.titlewin.refresh()

    def statusRefresh(self):
        n = self.current_cursor

        status_str = 'Press b or p to return to listings...'
        #if self.mycfg.get('curses_debug'):
        #    status_str = "nlines=%s, dlen=%s, rlen=%s, cc=%s, rc=%s" % \
        #               ( ( curses.LINES-4), len(self.data), len(self.records),
        #                   self.current_cursor, self.record_cursor )

        # And write the status
        try:
            self.statuswin.addnstr(0,0,status_str,curses.COLS-2,curses.A_BOLD)
        except:
            raise Exception, debug_str
        self.statuswin.refresh()
