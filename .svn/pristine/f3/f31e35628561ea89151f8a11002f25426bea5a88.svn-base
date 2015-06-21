#!/usr/bin/env python

from mlbConstants import *
from mlbListWin import MLBListWin
import curses

class MLBClassicsMenuWin(MLBListWin):

    def __init__(self,myscr,mycfg,data):
        self.myscr = myscr
        self.mycfg = mycfg
        self.data = data
        self.records = self.data[0:curses.LINES-4]
        self.record_cursor = 0
        self.current_cursor = 0
        self.statuswin = curses.newwin(1,curses.COLS-1,curses.LINES-1,0)
        self.titlewin = curses.newwin(2,curses.COLS-1,0,0)


    def Splash(self):
        lines = ('mlbclassics', VERSION, URL)
        for i in xrange(len(lines)):
            self.myscr.addnstr(curses.LINES/2+i, (curses.COLS-len(lines[i]))/2,                                lines[i],curses.COLS-2)
        self.myscr.refresh()


    def Refresh(self):
        if len(self.data) == 0:
            self.titlewin.refresh()
            self.myscr.refresh()
            self.statuswin.refresh()
            return

        self.myscr.clear()
        for n in range(curses.LINES-4):
            cursesflags = 0
            if n < len(self.records):
                s = self.records[n]['title']
                padding = curses.COLS - ( len(s) + 1 )
                if n == self.current_cursor:
                    s += ' '*padding
                if self.records[n].has_key('all'):
                    cursesflags |= curses.A_BOLD
            else:
                s = ' '*(curses.COLS-1)
            if n == self.current_cursor:
                cursesflags |= curses.A_REVERSE

            if n < len(self.records):
                self.myscr.addnstr(n+2, 0, s, curses.COLS-2, cursesflags)
            else:
                self.myscr.addnstr(n+2, 0, s, curses.COLS-2, cursesflags)
        self.myscr.refresh()


    def titleRefresh(self,mysched=None):
        titleStr = 'MLB CLASSIC CONTENT PLAYLISTS'
        padding = curses.COLS - (len(titleStr) + 6)
        titleStr += ' '*padding
        pos = curses.COLS - 6
        self.titlewin.clear()
        self.titlewin.addstr(0,0,titleStr)
        self.titlewin.addstr(0,pos,'M', curses.A_BOLD)
        self.titlewin.addstr(0,pos+1, 'enu')
        self.titlewin.hline(1, 0, curses.ACS_HLINE, curses.COLS-1)
        self.titlewin.refresh()


    def statusRefresh(self):
        if len(self.records) == 0:
            status_str = "No listings available."
            self.statuswin.clear()
            self.statuswin.addnstr(0,0,status_str,curses.COLS-2)
            self.statuswin.refresh()
            return
        posStr = "%s of %s" % ( self.current_cursor + self.record_cursor + 1,
                                len(self.data) )
        authorStr = "[%s]" % self.records[self.current_cursor]['author']
        sortStr = "[Sort:%s]" % self.mycfg.get('entry_sort')[:7]
        if self.mycfg.get('debug'):
            debugStr = '[DEBUG]'
        else:
            debugStr = ''
        statusStrLen = len(posStr) + len(authorStr) + len(sortStr) + len(debugStr) + 2
        padding = curses.COLS - statusStrLen
        statusStr=posStr + ' '*padding + debugStr + authorStr + sortStr
        if padding < 0:
            statusStr=statusStr[:padding]
        self.statuswin.addnstr(0,0,statusStr,curses.COLS-2,curses.A_BOLD)
        self.statuswin.refresh()


