#!/usr/bin/env python

import curses
import curses.textpad
import re
import time
from mlbListWin import MLBListWin
from mlbConstants import *

class MLBInningWin(MLBListWin):

    def __init__(self,myscr,mycfg,data,mysched):
        self.data = data
        self.mycfg = mycfg
        self.myscr = myscr
        self.mysched = mysched
        self.statuswin = curses.newwin(1,curses.COLS-1,curses.LINES-1,0)
        self.titlewin = curses.newwin(2,curses.COLS-1,0,0)
        self.innings = dict()
        self.logfile = LOGFILE.replace('log', 'innwin.log')
        self.log = open(self.logfile, "w")

    def Debug(self):
        self.statuswin.clear()
        self.statuswin.addnstr(0,0,'Press any key to return to listings...',
                               curses.COLS-2, curses.A_BOLD)
        self.myscr.clear()
        this_event = self.data[2][0][3]
        self.titlewin.clear()
        self.titlewin.addnstr(0,0,'INNINGS DEBUG FOR %s'%this_event, 
                              curses.COLS-2)
        self.titlewin.hline(1, 0, curses.ACS_HLINE, curses.COLS-1)
        self.myscr.addstr(2,0,repr(self.innings))
        self.myscr.refresh()
        self.statuswin.refresh()
        self.titlewin.refresh()
        self.myscr.getch()
        
    def resize(self):
        self.statuswin.mvwin(curses.LINES-1,0)
        self.statuswin.resize(1,curses.COLS-1)
        self.titlewin.mvwin(0, 0)
        self.titlewin.resize(2,curses.COLS-1)


    def Refresh(self):
        streamtype = 'video'
        if len(self.data) == 0:
            self.statuswin.addnstr(0,0,
                                   'No innings data available for this game',
                                   curses.COLS-2)
            self.statuswin.refresh()
            return

        self.statuswin.clear()
        self.statuswin.addnstr(0,0,'Fetching innings index...',curses.COLS-2)
        self.statuswin.refresh()
        self.myscr.clear()
        try:
            try:
                this_event = self.data[2][0][3]
            except:
                raise Exception,'Innings list is not availale for this game.'
            self.innings = self.mysched.parseInningsXml(this_event,
                                                     self.mycfg.get('use_nexdef'))
        except Exception,detail:
            #raise
            self.myscr.clear()
            self.myscr.addnstr(2,0,'Could not parse innings: ',curses.COLS-2)
            self.myscr.addstr(3,0,str(detail))
            self.myscr.refresh()
            #time.sleep(3)
            return
  
        # print header first:
        self.myscr.clear()

        # skip a line
        self.myscr.addnstr(2,0,'Enter T or B for top or bottom plus inning to jump to.',curses.COLS-2)
        self.myscr.addnstr(3,0,'Example: T6 to jump to Top of 6th inning.',curses.COLS-2)
        self.myscr.addnstr(4,0,'Enter E for Extra Innings.',curses.COLS-2)
        self.myscr.addnstr(5,0,'Press <Enter> to return to listings.',curses.COLS-2)
        # skip a line, print top half innings
        inn_str = ' '*5 + '[1] [2] [3] [4] [5] [6] [7] [8] [9]'
        latest = 0
        city_str = dict()
        for city in ( 'away', 'home' ):
            team = self.data[0][city].upper()
            city_str[city] = '%-3s '%team
            for i in range(len(self.innings)):
                # zero reserved for pre-game
                if i == 0:
                    continue
                if self.innings.has_key(i): 
                    if i > 9:
                       if i > latest:
                           latest = i
                       continue
                    if self.innings[i].has_key(city):
                        # no spoilers for home victories
                        if i == 9 and city == 'home':
                            city_str[city] += ' [?]'
                        else:
                            city_str[city] += ' [+]'
                        if i >= latest:
                            latest = i
                    else:
                        if i == 9 and city == 'home':
                            city_str[city] += ' [?]'
                        else:
                            city_str[city] += ' [-]'
                else:
                    city_str[city] += ' [-]'
        if self.mycfg.get('show_inning_frames'):
            self.myscr.addnstr(7,0,'[+] = Half inning is available',curses.COLS-2)
            self.myscr.addnstr(8,0,'[-] = Half inning is not available',curses.COLS-2)
            self.myscr.addnstr(9,0,'[?] = Bottom of 9th availability is never shown to avoid spoilers',curses.COLS-2)
            self.myscr.addnstr(12,0,inn_str,curses.COLS-2)
            self.myscr.addnstr(14,0,city_str['away'],curses.COLS-2)
            self.myscr.addnstr(16,0,city_str['home'],curses.COLS-2)
        latest_str = 'Last available half inning is: '
        if latest == 0:
            latest_str += 'None'
        elif self.data[5] in ('F', 'CG', 'GO'):
            # remove spoiler of home victories
            latest_str += 'Game Completed'
        elif not self.innings[latest].has_key('home'):
            latest_str += 'Top ' + str(latest)
        else:
            latest_str += 'Bot ' + str(latest)
        self.myscr.addnstr(curses.LINES-3,0,latest_str,curses.COLS-2)
        self.myscr.refresh()

    def selectToPlay(self):
        jump_prompt = 'Enter half inning to jump to: '
        jump = self.prompter(self.statuswin, jump_prompt)
        if jump == '':
            # return to listings
            return
        jump_pat = re.compile(r'(B|T|E|D)(\d+)?')
        match = re.search(jump_pat, jump.upper())
        if match is None:
            self.statuswin.clear()
            self.statuswin.addstr(0,0,'You have entered invalid half inning.')
            self.statuswin.refresh()
            time.sleep(2)
            return
        elif match.groups()[0] == 'D':
            self.Debug()
            return
        elif match.groups()[0] == 'E':
            inning = 10
            half = 'away'
        elif match.groups()[1] is None:
            self.statuswin.clear()
            self.statuswin.addstr(0,0,'You have an entered invalid half inning.',curses.A_BOLD)
            self.statuswin.refresh()
            time.sleep(2)
            return
        elif match.groups()[0] == 'B':
            self.log.write('Matched ' + match.groups()[1] + ' inning.\n')
            inning = int(match.groups()[1]) 
            half = 'home'
        elif match.groups()[0] == 'T':
            self.log.write('Matched ' + match.groups()[1] + ' inning.\n')
            inning = int(match.groups()[1])
            half = 'away'
        try:
            start_time = self.innings[inning][half]
        except KeyError:
            self.statuswin.clear()
            self.statuswin.addnstr(0,0,'You have entered an invalid half inning.',curses.COLS-2,curses.A_BOLD)
            self.statuswin.refresh()
            time.sleep(3)
            return
        except UnboundLocalError:
            raise Exception,repr(self.innings)
        self.log.write('Selected start_time = ' + str(start_time) + '\n')
        self.statusRefresh('Requesting media stream with start at %s'%str(start_time))
        audio = False
        return start_time

                
    def titleRefresh(self):
        if len(self.data) == 0:
            titlestr = 'ERROR OCCURRED IN JUMP TO INNINGS:'
        else:
            titlestr =  'JUMP TO HALF INNINGS: '
            titlestr += str(self.data[6])

        padding = curses.COLS - (len(titlestr) + 6)
        titlestr += ' '*padding
        pos = curses.COLS - 6
        self.titlewin.addstr(0,0,titlestr)
        self.titlewin.addstr(0,pos,'H', curses.A_BOLD)
        self.titlewin.addstr(0,pos+1, 'elp')
        self.titlewin.hline(1, 0, curses.ACS_HLINE, curses.COLS-1)
        self.titlewin.refresh()

    def statusRefresh(self,status_str=None):
        if status_str == None:
            status_str = 'Press L to return to listings...'

        # And write the status
        try:
            self.statuswin.addnstr(0,0,status_str,curses.A_BOLD,curses.COLS-2)
        except:
            rows = curses.LINES
            cols = curses.COLS
            slen = len(status_str)
            raise Exception,'(' + str(slen) + '/' + str(cols) + ',' + str(n) + '/' + str(rows) + ') ' + status_str
        self.statuswin.refresh()
