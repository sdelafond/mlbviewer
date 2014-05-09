#!/usr/bin/env python

from mlbListWin import MLBListWin
from mlbStandings import MLBStandings
import curses
from datetime import datetime
from mlbGameTime import MLBGameTime

class MLBStandingsWin(MLBListWin):

    def __init__(self,myscr,mycfg,data,last_update,year):
        self.stdata = data
        self.last_update = last_update
        self.year = year
        self.data = []
        self.records = []
        self.mycfg = mycfg
        self.myscr = myscr
        self.current_cursor = 0
        self.record_cursor = 0
        self.statuswin = curses.newwin(1,curses.COLS-1,curses.LINES-1,0)
        self.titlewin = curses.newwin(2,curses.COLS-1,0,0)

    def Refresh(self):
        if len(self.stdata) == 0:
            self.titlewin.refresh()
            self.myscr.refresh()
            self.statuswin.refresh()
            return

        self.myscr.clear()
        self.data = []
        self.prepareStandings()
        self.records = self.data[self.record_cursor:self.record_cursor+curses.LINES-4]
        n = 0
        for s in self.records:
            text = s[0]
            if n == self.current_cursor:
                pad = curses.COLS-1 - len(text)
                if pad > 0:
                    text += ' '*pad
                try:
                    self.myscr.addnstr(n+2,0,text,curses.COLS-2,
                                       s[1]|curses.A_REVERSE)
                except:
                    raise Exception,repr(s)
            else:
                self.myscr.addnstr(n+2,0,text,curses.COLS-2,s[1])
            n+=1
        self.myscr.refresh()

    def prepareStandings(self):
        std_fmt = "%-16s %5s %5s %5s %5s %4s %5s %5s %4s %6s %6s %4s %4s %4s"
        for standing in self.stdata:
            division = standing[0]
            standings = standing[1]
            # except for the first line, prepend a blank line between 
            # divisions
            if len(self.data) > 0:
                self.data.append((" ",0))
            self.data.append((division,curses.A_BOLD))
            header_str = std_fmt % \
                       ( 'TEAM', 'W', 'L', 'WP', 'GB','E#', 'WCGB', 'L10', 'STRK',
                         'HOME', 'ROAD', 'RS', 'RA', '+/-')
            self.data.append((header_str,curses.A_BOLD))
            
            for team in standings:
                try:
                    rs = "%.1f" % ( float(team['RS']) / float(team['G']) )
                    ra = "%.1f" % ( float(team['RA']) / float(team['G']) )
                except ZeroDivisionError:
                    rs = 0.0
                    ra = 0.0
                dif = "%.1f" % ( float(rs) - float(ra) )
                team_str = std_fmt % \
                       ( team['first'],
                         team['W'], team['L'], team['WP'],
                         team['GB'],
                         team['E'], team['WCGB'],
                         team['L10_W']+ '-' +team['L10_L'],
                         team['STRK'],
                         team['HW']+'-'+team['HL'],
                         team['AW']+'-'+team['AL'] ,
                         str(rs), str(ra), str(dif) )
                if team['file_code'] in self.mycfg.get('favorite'):
                    if self.mycfg.get('use_color'):
                        self.data.append((team_str,curses.color_pair(1)))
                    else:
                        self.data.append((team_str,curses.A_UNDERLINE))
                else:
                    self.data.append((team_str,0))

    def titleRefresh(self,mysched):
        if len(self.stdata) == 0:
            titlestr = "STANDINGS NOT AVAILABLE"
        else:
            upd = datetime.strptime(self.last_update, "%Y-%m-%dT%H:%M:%S-04:00")
            gametime=MLBGameTime(upd,self.mycfg.get('time_offset'))
            update_datetime = gametime.localize()
            update_str = update_datetime.strftime('%Y-%m-%d %H:%M:%S')
            titlestr = "STANDINGS: Last updated: %s" % update_str
            #titlestr += " (updates only once a day)"
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
        pad_len = (curses.COLS-2) - ( len(status_str) + len(str(self.year))+2 )
        if self.mycfg.get('curses_debug'):
            status_str = 'd_len=%s, r_len=%s, cc=%s, rc=%s, cl_-4: %s' %\
                ( str(len(self.data)), str(len(self.records)),
                  str(self.current_cursor), str(self.record_cursor),
                  str(curses.LINES-4) )

        status_str += pad_len*' ' + '[%s]'%self.year
        # And write the status
        try:
            self.statuswin.addnstr(0,0,status_str,curses.COLS-2,curses.A_BOLD)
        except:
            rows = curses.LINES
            cols = curses.COLS
            slen = len(status_str)
            raise Exception,'(' + str(slen) + '/' + str(cols) + ',' + str(n) + '/' + str(rows) + ') ' + status_str
        self.statuswin.refresh()
