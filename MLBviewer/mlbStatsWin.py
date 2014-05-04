#!/usr/bin/env python

from mlbListWin import MLBListWin
from mlbStats import MLBStats
import curses
from datetime import datetime
from mlbSchedule import gameTimeConvert
from mlbConstants import *

class MLBStatsWin(MLBListWin):

    def __init__(self,myscr,mycfg,data,last_update):
        self.data = data
        self.mycfg = mycfg
        self.last_update = last_update
        self.records = []
        self.myscr = myscr
        self.current_cursor = 0
        self.record_cursor = 0
        self.statuswin = curses.newwin(1,curses.COLS-1,curses.LINES-1,0)
        self.titlewin = curses.newwin(3,curses.COLS-1,0,0)
        self.fmt = dict()
        self.hdr = dict()
        self.fmt['hitting'] = []
        self.fmt['pitching'] = []
        self.hdr['hitting'] = []
        self.hdr['pitching'] = []
        self.fmt['hitting'].append("%-2s %-12s %4s %3s %3s %3s %3s %3s %3s %3s %3s %3s %3s %3s %3s %3s %4s %4s %4s %5s")
        # All-Time Stats need wider field pads
        self.fmt['hitting'].append("%-2s %-12s %4s %3s %4s %5s %4s %4s %3s %3s %3s %4s %4s %4s %3s %3s %4s %4s %4s %5s")
        # Career is different still replacing rank with year and no name
        self.fmt['hitting'].append("%-4s%1s%4s%1s%4s %5s %4s %4s %3s %3s %3s %4s %4s %4s %3s %3s %4s %4s %4s %5s")
        self.hdr['hitting'].append(self.fmt['hitting'][0] % \
                   ( 'RK', 'Player', 'Team', 'Pos', 'G', 'AB', 'R', 'H',
                     '2B', '3B', 'HR', 'RBI', 'BB', 'SO', 'SB', 'CS', 
                     'AVG', 'OBP', 'SLG', 'OPS' ) )
        self.hdr['hitting'].append(self.fmt['hitting'][1] % \
                   ( 'RK', 'Player', 'Team', 'Pos', 'G', 'AB', 'R', 'H',
                     '2B', '3B', 'HR', 'RBI', 'BB', 'SO', 'SB', 'CS', 
                     'AVG', 'OBP', 'SLG', 'OPS' ) )
        self.hdr['hitting'].append(self.fmt['hitting'][2] % \
                   ( 'Year', ' ', 'Team', ' ', 'G', 'AB', 'R', 'H',
                     '2B', '3B', 'HR', 'RBI', 'BB', 'SO', 'SB', 'CS', 
                     'AVG', 'OBP', 'SLG', 'OPS' ) )
        self.fmt['pitching'].append("%-2s %-10s %4s %3s %3s %4s %3s %3s %3s %3s %5s %4s %3s %3s %3s %3s %3s %4s %4s")
        self.fmt['pitching'].append("%-2s %-10s %4s %3s %3s %4s %4s %3s %3s %3s %6s %4s %4s %4s %3s %4s %4s %4s %4s")
        self.fmt['pitching'].append("%-4s%1s%4s %3s %3s %4s %4s %3s %3s %3s %6s %4s %4s %4s %3s %4s %4s %4s %4s")
        self.hdr['pitching'].append(self.fmt['pitching'][0] % \
                   ( 'RK', 'Player', 'Team', 'W', 'L', 'ERA', 'G', 'GS',
                     'SV', 'SVO', 'IP', 'H', 'R', 'ER', 'HR', 'BB', 
                     'SO', 'AVG', 'WHIP' ))
        self.hdr['pitching'].append(self.fmt['pitching'][1] % \
                   ( 'RK', 'Player', 'Team', 'W', 'L', 'ERA', 'G', 'GS',
                     'SV', 'SVO', 'IP', 'H', 'R', 'ER', 'HR', 'BB', 
                     'SO', 'AVG', 'WHIP' ))
        self.hdr['pitching'].append(self.fmt['pitching'][2] % \
                   ( 'Year', ' ', 'Team', 'W', 'L', 'ERA', 'G', 'GS',
                     'SV', 'SVO', 'IP', 'H', 'R', 'ER', 'HR', 'BB', 
                     'SO', 'AVG', 'WHIP' ))

    def Refresh(self):
        if len(self.data) == 0:
            self.titlewin.refresh()
            self.myscr.refresh()
            self.statuswin.refresh()
            return

        self.myscr.clear()
        self.records = self.data[self.record_cursor:self.record_cursor+curses.LINES-5]
        self.type = self.mycfg.get('stat_type')
        self.sort = self.mycfg.get('sort_column')
        n = 0
        for rec in self.records:
            if self.type == 'hitting':
                s = self.prepareHittingStats(rec,self.type,self.sort)
            else:
                try:
                    s = self.preparePitchingStats(rec,self.type,self.sort)
                except KeyError:
                    raise
                    raise Exception,rec
       
            try:
                text = s[0]
            except:
                raise Exception,"%s:%s" % (self.type,self.sort)
            if n == self.current_cursor:
                pad = curses.COLS-1 - len(text)
                if pad > 0:
                    text += ' '*pad
                try:
                    self.myscr.addnstr(n+3,0,text,curses.COLS-2,
                                       s[1]|curses.A_REVERSE)
                except:
                    raise Exception,repr(s)
            else:
                self.myscr.addnstr(n+3,0,text,curses.COLS-2,s[1])
            n+=1
        self.myscr.refresh()

    def prepareHittingStats(self,player,statType='hitting', sortColumn='avg'):
        self.season_type = self.mycfg.get('season_type')
        self.player = int(self.mycfg.get('player_id'))
        if self.player > 0:
            wid=2
            rank_or_year = player['season']
            name_or_space = ' '
            pos_or_space = ' '
        elif self.season_type == 'ALL':
            wid=1
            rank_or_year = player['rank']
            name_or_space = player['name_display_last_init'][:12]
            pos_or_space = player['pos']
        else:
            wid=0
            rank_or_year = player['rank']
            name_or_space = player['name_display_last_init'][:12]
            pos_or_space = player['pos']
        playerStr = self.fmt['hitting'][wid] % \
               ( rank_or_year, name_or_space,
                 player['team_abbrev'], pos_or_space, player['g'],
                 player['ab'], player['r'], player['h'], player['d'],
                 player['t'], player['hr'], player['rbi'], 
                 player['bb'], player['so'], player['sb'], 
                 player['cs'], player['avg'], player['obp'], 
                 player['slg'], player['ops'] )
                     
        team = STATS_TEAMS[int(player['team_id'])]
        if team in self.mycfg.get('favorite'):
            if self.mycfg.get('use_color'):
                return (playerStr,curses.color_pair(1))
            else:
                return (playerStr,curses.A_UNDERLINE)
        else:
            return (playerStr,0)

    def preparePitchingStats(self,player,statType='pitching',sortColumn='era'):
        self.season_type = self.mycfg.get('season_type')
        self.player = int(self.mycfg.get('player_id'))
        if self.player > 0:
            wid=2
            try:
                rank_or_year = player['season']
                name_or_space = ' '
            except:
                raise Exception,player
        elif self.season_type == 'ALL':
            wid=1
            rank_or_year = player['rank']
            name_or_space = player['name_display_last_init'][:10]
        else:
            wid=0
            rank_or_year = player['rank']
            name_or_space = player['name_display_last_init'][:10]
        playerStr = self.fmt['pitching'][wid] % \
               ( rank_or_year, name_or_space,
                 player['team_abbrev'], player['w'], player['l'],
                 player['era'][:4], player['g'], player['gs'], player['sv'],
                 player['svo'], player['ip'], player['h'], 
                 player['r'], player['er'], 
                 player['hr'], player['bb'], 
                 player['so'], player['avg'][:4], player['whip'] )
                 
        try:
            team = STATS_TEAMS[int(player['team_id'])]
        except:
            STATS_TEAMS[int(player['team_id'])] = player['team_abbrev']
            team = STATS_TEAMS[int(player['team_id'])]
        if team in self.mycfg.get('favorite'):
            if self.mycfg.get('use_color'):
                return (playerStr,curses.color_pair(1))
            else:
                return (playerStr,curses.A_UNDERLINE)
        else:
            return (playerStr,0)

    def titleRefresh(self,mysched=None):
        self.player = int(self.mycfg.get('player_id'))
        if len(self.data) == 0:
            titlestr = "STATS NOT AVAILABLE"
        else:
            try:
                upd = datetime.strptime(self.last_update, "%Y-%m-%dT%H:%M:%S-04:00")
            except:
                upd = datetime.strptime(self.last_update, "%Y-%m-%dT%H:%M:%S")
            update_datetime = gameTimeConvert(upd)
            update_str = update_datetime.strftime('%Y-%m-%d %H:%M:%S')
            self.type = self.mycfg.get('stat_type')
            type = self.type.upper()
            sort = self.mycfg.get('sort_column').upper()
            order = STATS_SORT_ORDER[int(self.mycfg.get('sort_order'))].upper()
            team =  int(self.mycfg.get('sort_team'))
            if team > 0:
                league_str = STATS_TEAMS[team].upper()
            else:
                league_str = self.mycfg.get('league')
            
            titlestr = "%s STATS (%s:%s) SORT ORDER: %s" % ( type, league_str, 
                                                             sort, order )
            if self.player > 0:
                titlestr = "CAREER STATS FOR: %s"%self.mycfg.get('player_name')
        padding = curses.COLS - (len(titlestr) + 6)
        titlestr += ' '*padding
        pos = curses.COLS - 6
        self.titlewin.addstr(0,0,titlestr)
        self.titlewin.addstr(0,pos,'H', curses.A_BOLD)
        self.titlewin.addstr(0,pos+1, 'elp')
        self.titlewin.hline(1, 0, curses.ACS_HLINE, curses.COLS-1)
        self.season_type = self.mycfg.get('season_type')
        if self.player > 0:
            wid=2
        elif self.season_type == 'ALL':
            wid=1
        else:
            wid=0
        self.titlewin.addnstr(2,0,self.hdr[self.type][wid],curses.COLS-2,curses.A_BOLD)
        self.titlewin.refresh()

    def statusRefresh(self):
        n = self.current_cursor

        #upd = datetime.strptime(self.last_update, "%Y-%m-%dT%H:%M:%S-04:00")
        try:
            upd = datetime.strptime(self.last_update, "%Y-%m-%dT%H:%M:%S-04:00")
        except:
            upd = datetime.strptime(self.last_update, "%Y-%m-%dT%H:%M:%S")
        update_datetime = gameTimeConvert(upd)
        update_str = update_datetime.strftime('%Y-%m-%d %H:%M:%S')
        status_str = "Last Updated: %s" % update_str
        if self.mycfg.get('season_type') == 'ANY':
            #season_str = "[%4s]" % update_datetime.year
            season_str = "[%4s]" % self.mycfg.get('season')
        else:
            if int(self.mycfg.get('active_sw')):
                season_str = "[ACTV]"
            else:
                season_str = "[ALL ]"
        if self.mycfg.get('curses_debug'):
            status_str = 'd_len=%s, r_len=%s, cc=%s, rc=%s, cl_-4: %s' %\
                ( str(len(self.data)), str(len(self.records)),
                  str(self.current_cursor), str(self.record_cursor),
                  str(curses.LINES-4) )

        padding = (curses.COLS-2)- (len(status_str) + len(season_str))
        status_str += ' '*padding + season_str
        # And write the status
        try:
            self.statuswin.addnstr(0,0,status_str,curses.COLS-2,curses.A_BOLD)
        except:
            rows = curses.LINES
            cols = curses.COLS
            slen = len(status_str)
            raise Exception,'(' + str(slen) + '/' + str(cols) + ',' + str(n) + '/' + str(rows) + ') ' + status_str
        self.statuswin.refresh()

    def resize(self):
        try:
            self.statuswin.clear()
            self.statuswin.mvwin(curses.LINES-1,0)
            self.statuswin.resize(1,curses.COLS-1)
            self.titlewin.mvwin(0,0)
            self.titlewin.resize(3,curses.COLS-1)
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
