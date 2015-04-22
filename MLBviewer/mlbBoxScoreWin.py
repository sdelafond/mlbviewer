#!/usr/bin/env python

import curses
import time
from mlbListWin import MLBListWin
from mlbConstants import *
from xml.dom.minidom import parseString
import xml.dom.minidom

class MLBBoxScoreWin(MLBListWin):

    def __init__(self,myscr,mycfg,data):
        self.boxdata = data
        self.data = []
        self.records = []
        self.mycfg = mycfg
        self.myscr = myscr
        self.current_cursor = 0
        self.record_cursor = 0
        self.statuswin = curses.newwin(1,curses.COLS-1,curses.LINES-1,0)
        self.titlewin = curses.newwin(2,curses.COLS-1,0,0)

    def Refresh(self):
        if len(self.boxdata) == 0:
            self.titlewin.refresh()
            self.myscr.refresh()
            self.statuswin.refresh()
            return

        self.myscr.clear()
        self.data = []
        self.prepareBattingLines('away')
        if len(self.data) > 0:
            self.data.append(('',0,None))
        for blob in self.boxdata['batting']['away']['batting-data']:
            self.parseDataBlob(blob)
        self.prepareBattingLines('home')
        if len(self.data) > 0:
            self.data.append(('',0,None))
        for blob in self.boxdata['batting']['home']['batting-data']:
            self.parseDataBlob(blob)
        self.preparePitchingLines('away')
        if len(self.data) > 0:
            self.data.append(('',0,None))
        for blob in self.boxdata['pitching']['away']['pitching-data']:
            self.parseDataBlob(blob)
        self.preparePitchingLines('home')
        if len(self.data) > 0:
            self.data.append(('',0,None))
        for blob in self.boxdata['pitching']['home']['pitching-data']:
            self.parseDataBlob(blob)
        if len(self.data) > 0:
            self.data.append(('',0,None))
        self.parseDataBlob(self.boxdata['game_info'])

        # all the lines above created the self.data list, slice it to visible
        self.records = self.data[self.record_cursor:self.record_cursor+curses.LINES-4]
        n = 0
        for s in self.records:
            text=s[0]
            if n == self.current_cursor:
                pad = curses.COLS-1 - len(text)
                if pad > 0:
                    text += ' '*pad
                self.myscr.addnstr(n+2,0,text,curses.COLS-2,
                                   s[1]|curses.A_REVERSE)
            else:
                self.myscr.addnstr(n+2,0,text,curses.COLS-2,s[1])
            n+=1
        self.myscr.refresh()

    def titleRefresh(self,mysched):
        if len(self.boxdata) == 0:
            titlestr = "NO BOX SCORE AVAILABLE FOR THIS GAME"
        else:
            (year,month,day) = self.boxdata['game']['game_id'].split('/')[:3]
            titlestr = "BOX SCORE FOR  " +\
                self.boxdata['game']['game_id'] +\
                ' (' +\
                str(month) + '/' +\
                str(day) + '/' +\
                str(year) +\
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
        if self.mycfg.get('curses_debug'):
            status_str = 'd_len=%s, r_len=%s, cc=%s, rc=%s, cl_-4: %s' %\
                 ( str(len(self.data)), str(len(self.records)),
                   str(self.current_cursor), str(self.record_cursor),
                   str(curses.LINES-4) )

        # And write the status
        try:
            self.statuswin.addnstr(0,0,status_str,curses.COLS-2,curses.A_BOLD)
        except:
            rows = curses.LINES
            cols = curses.COLS
            slen = len(status_str)
            raise Exception,'(' + str(slen) + '/' + str(cols) + ',' + str(n) + '/' + str(rows) + ') ' + status_str
        self.statuswin.refresh()

    # let's avoid a big indented for loop and require the team as an arg
    def preparePitchingLines(self,team):
        DOTS_LEN=34
        # shorten the path
        pitching = self.boxdata['pitching'][team]
        PITCHING_STATS = ( 'IP', 'H', 'R', 'ER', 'BB', 'SO', 'HR', ' ERA' )
        header_str = self.boxdata['game'][team+'_sname']
        header_str += ' Pitching'
        dots = DOTS_LEN - len(header_str)
        header_str += ' ' + dots*'.'
        for stat in PITCHING_STATS:
            header_str += '%5s' % stat
        team_tuple=( self.boxdata['game'][team + '_id'],
                     0,
                     self.boxdata['game'][team + '_fname'] )
        self.data.append((header_str,curses.A_BOLD,team_tuple))
        #self.data.append(('',0))
        for pitcher in pitching['pitchers']['pitching-order']:
            name_str = pitching['pitchers'][pitcher]['name']
            # pitching note is W, L, SV info
            if pitching['pitchers'][pitcher].has_key('note'):
                name_str += ' ' + pitching['pitchers'][pitcher]['note']
            dots = DOTS_LEN - len(name_str)
            name_str += ' ' + dots*'.'
            for stat in PITCHING_STATS:
                if stat == 'IP':
                    ip = str(int(pitching['pitchers'][pitcher]['out'])/3)
                    ip += '.'
                    ip += str(int(pitching['pitchers'][pitcher]['out'])%3)
                    name_str += '%5s' % ip
                elif stat == ' ERA':
                    name_str += '%6s' % pitching['pitchers'][pitcher]['era']
                else:
                    name_str += '%5s' % pitching['pitchers'][pitcher][stat.lower()]
            # second item is player type: 0=pitcher, 1=batter
            player_tuple=(pitching['pitchers'][pitcher]['id'],
                          0,
                          pitching['pitchers'][pitcher]['name_display_first_last'])
            self.data.append((name_str,0,player_tuple))
        # print totals
        totals_str = 'Totals'
        dots = DOTS_LEN - len(totals_str)
        totals_str += ' ' + dots*'.'
        for stat in PITCHING_STATS:
            if stat == 'IP':
                ip = str(int(pitching['out'])/3)
                ip += '.'
                ip += str(int(pitching['out'])%3)
                totals_str += '%5s' % ip
            elif stat == ' ERA':
                totals_str += '%6s' % pitching['era']
            else:
                totals_str += '%5s' % pitching[stat.lower()]
        #self.data.append(('',0))
        self.data.append((totals_str,curses.A_BOLD,None))
        

    # let's avoid a big indented for loop and require the team as an arg
    def prepareBattingLines(self,team):
        DOTS_LEN=34
        # shorten the path
        batting = self.boxdata['batting'][team]

        # build the batting order first
        battingOrder = dict()
        for batter_id in batting['batters']:
            try:
                order = int(batting['batters'][batter_id]['bo'])
                battingOrder[order] = batter_id
            except:
                continue
        batters = battingOrder.keys()
        batters = sorted(batters, key=int)

        BATTING_STATS=( 'AB', 'R', 'H', 'RBI', 'BB', 'SO', 'LOB', 'AVG')
        # first a header line
        header_str = self.boxdata['game'][team+'_sname']
        header_str += ' Batting'
        dots = DOTS_LEN - len(header_str)
        header_str += ' ' + dots*'.'
        for stat in BATTING_STATS:
            header_str += '%5s' % stat
        team_tuple=( self.boxdata['game'][team + '_id'],
                     1,
                     self.boxdata['game'][team + '_fname'] )
        self.data.append((header_str,curses.A_BOLD,team_tuple))
        #self.data.append(('',0))

        # now the batters in the order just built
        for bo in batters:
            batter_id = battingOrder[bo]
            name_str = batting['batters'][batter_id]['name']
            name_str += ' '
            name_str += batting['batters'][batter_id]['pos']
            # indent if a substitution
            if bo % 100 > 0:
                if batting['batters'][batter_id].has_key('note'):
                    name_str = batting['batters'][batter_id]['note'] + name_str
                    name_str = ' ' + name_str
            dots=DOTS_LEN - len(name_str)
            name_str += ' ' + dots*'.'
            # now the stats
            for stat in BATTING_STATS:
                name_str += '%5s' % batting['batters'][batter_id][stat.lower()]
            # second item is player type: 0=pitcher, 1=batter
            player_tuple=(batting['batters'][batter_id]['id'],
                          1,
                          batting['batters'][batter_id]['name_display_first_last'])
            self.data.append((name_str,0,player_tuple))
        #self.data.append(('',0))
        # print totals
        totals_str = 'Totals'
        dots = DOTS_LEN - len(totals_str)
        totals_str += ' ' + dots*'.'
        for stat in BATTING_STATS:
            totals_str += '%5s' % batting[stat.lower()]
        self.data.append((totals_str,curses.A_BOLD,None))
        # and the batting-note...
        if len(batting['batting-note']) > 0:
            self.data.append(('',0,None))
            for bnote in batting['batting-note']:
                # batting-note can be multi-line, break it naturally
                if len(str(bnote)) > curses.COLS-1:
                    tmp = ''
                    for word in str(bnote).split(' '):
                        if len(tmp) + len(word) + 1 < curses.COLS-1:
                            tmp += word + ' '
                        else:
                            self.data.append((tmp.strip(),0,None))
                            tmp = word + ' '
                    self.data.append((tmp.strip(),0,None))
                    tmp = ''
                else:
                    self.data.append((str(bnote),0,None))

    def parseDataBlob(self,blob):
        data='<data>'+blob.childNodes[0].data+'</data>'
        dptr=parseString(data)
        tmp_str=''
        for elem in dptr.childNodes[0].childNodes:
            if elem.nodeName == 'b':
                tmp_str += elem.childNodes[0].nodeValue
            elif elem.nodeName == 'span':
                for c_elem in elem.childNodes:
                    if c_elem.nodeName == 'b':
                        tmp_str += c_elem.childNodes[0].nodeValue
                    elif c_elem.nodeType == elem.TEXT_NODE:
                        if c_elem.nodeValue.isspace():
                            continue
                        if len(tmp_str) + len(c_elem.nodeValue) > curses.COLS-1:
                            tmp_str1 = tmp_str + ' '
                            for word in c_elem.nodeValue.split(' '):
                                if len(tmp_str1) + len(word) + 1 > curses.COLS-1:
                                    self.data.append((tmp_str1.strip(),0,None))
                                    tmp_str1 = word + ' '
                                else:
                                    tmp_str1 += word + ' '
                            # pack any remainder back into tmp_str
                            tmp_str = tmp_str1
                        else:
                            tmp_str += c_elem.nodeValue
                    elif c_elem.nodeName == 'br':
                        self.data.append((tmp_str,0,None))
                        tmp_str=''
            elif elem.nodeType == elem.TEXT_NODE:
                if elem.nodeValue.isspace():
                    continue
                if len(tmp_str) + len(elem.nodeValue) > curses.COLS-1:
                    tmp_str1 = tmp_str + ' '
                    for word in elem.nodeValue.split(' '):
                        if len(tmp_str1) + len(word) + 1 > curses.COLS-1:
                            self.data.append((tmp_str1.strip(),0,None))
                            tmp_str1 = word + ' '
                        else:
                            tmp_str1 += word + ' ' 
                    # pack any remainder back into tmp_str
                    tmp_str = tmp_str1
                else:
                    tmp_str += elem.nodeValue
            elif elem.nodeName == 'br':
                self.data.append((tmp_str,0,None))
                tmp_str=''

        
