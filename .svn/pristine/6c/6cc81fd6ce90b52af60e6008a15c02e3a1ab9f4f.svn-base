#!/usr/bin/env python

from mlbConstants import *
from mlbListWin import MLBListWin
import curses

class MLBDailyMenuWin(MLBListWin):

    def __init__(self,myscr,mycfg):
        self.myscr = myscr
        self.mycfg = mycfg
        self.data = sorted(MLBCOM_VIDTITLES.keys(),key=int)
        self.records = self.data[0:curses.LINES-4]
        self.record_cursor = 0
        self.current_cursor = 0
        self.statuswin = curses.newwin(1,curses.COLS-1,curses.LINES-1,0)
        self.titlewin = curses.newwin(2,curses.COLS-1,0,0)


    def Refresh(self):
        if len(self.data) == 0:
            self.titlewin.refresh()
            self.myscr.refresh()
            self.statuswin.refresh()
            return

        self.myscr.clear()
        for n in range(curses.LINES-4):
            if n < len(self.records):
                s = MLBCOM_VIDTITLES[self.records[n]]
                padding = curses.COLS - ( len(s) + 1 )
                if n == self.current_cursor:
                    s += ' '*padding
            else:
                s = ' '*(curses.COLS-1)
            if n == self.current_cursor:
                cursesflags = curses.A_REVERSE
            else:
                cursesflags = 0

            if n < len(self.records):
                self.myscr.addnstr(n+2, 0, s, curses.COLS-2, cursesflags)
            else:
                self.myscr.addnstr(n+2, 0, s, curses.COLS-2, cursesflags)
        self.myscr.refresh()


    def titleRefresh(self,mysched=None):
        titleStr = 'AVAILABLE CATEGORIES OF MLB.COM VIDEOS'
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
            status_str = "No listings available for this day."
            self.statuswin.clear()
            self.statuswin.addnstr(0,0,status_str,curses.COLS-2)
            self.statuswin.refresh()
            return
        statusStr = MLBCOM_VIDTITLES[self.records[self.current_cursor]]
        speedStr = SPEEDTOGGLE.get(str(self.mycfg.get('speed')))
        if self.mycfg.get('debug'):
            debugStr = '[DEBUG]'
        else:
            debugStr = ''
        statusStrLen = len(statusStr) + len(speedStr) + len(debugStr) + 2
        padding = curses.COLS - statusStrLen
        statusStr+=' '*padding + debugStr + speedStr
        if padding < 0:
            statusStr=statusStr[:padding]
        self.statuswin.addnstr(0,0,statusStr,curses.COLS-2,curses.A_BOLD)
        self.statuswin.refresh()


