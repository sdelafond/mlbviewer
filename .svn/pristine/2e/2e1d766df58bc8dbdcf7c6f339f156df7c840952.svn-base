#!/usr/bin/env python

import curses
import curses.textpad
import time
from mlbListWin import MLBListWin
from mlbConstants import *

class MLBTopWin(MLBListWin):

    def __init__(self,myscr,mycfg,data):
        self.data = data
        # data is everything, records is only what's visible
        self.records = []
        self.mycfg = mycfg
        self.myscr = myscr
        self.current_cursor = 0
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
                s = self.records[n][1]

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
                self.myscr.addnstr(n+2, 0, s, curses.COLS-2, cursesflags)
            else:
                self.myscr.addnstr(n+2, 0, s, curses.COLS-2 )

        self.myscr.refresh()

    def titleRefresh(self,mysched):
        if len(self.data) == 0:
            titlestr = "NO TOP PLAYS AVAILABLE FOR THIS GAME"
        else:
            titlestr = "TOP PLAYS AVAILABLE FOR " +\
                self.records[self.current_cursor][0] +\
                ' (' +\
                str(mysched.month) + '/' +\
                str(mysched.day) + '/' +\
                str(mysched.year) + ' ' +\
                ')'

        padding = curses.COLS - (len(titlestr) + 6)
        titlestr += ' '*padding
        pos = curses.COLS - 6
        self.titlewin.addstr(0,0,titlestr)
        self.titlewin.addstr(0,pos,'H', curses.A_BOLD)
        self.titlewin.addstr(0,pos+1, 'elp')
        self.titlewin.hline(1, 0, curses.ACS_HLINE, curses.COLS-1)
        self.titlewin.refresh()

    def statusRefresh(self):
        n = self.current_cursor

        status_str = 'Press L to return to listings...'

        # And write the status
        try:
            self.statuswin.addnstr(0,0,status_str,curses.COLS-2,curses.A_BOLD)
        except:
            rows = curses.LINES
            cols = curses.COLS
            slen = len(status_str)
            raise Exception,'(' + str(slen) + '/' + str(cols) + ',' + str(n) + '/' + str(rows) + ') ' + status_str
        self.statuswin.refresh()
