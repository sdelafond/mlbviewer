#!/usr/bin/env python

import curses
import curses.textpad
import time
from mlbListWin import MLBListWin
from mlbConstants import *

class MLBLineScoreWin(MLBListWin):

    def __init__(self,myscr,mycfg,data):
        self.data = data
        # data is everything, records is only what's visible
        self.records = []
        self.mycfg = mycfg
        self.myscr = myscr
        self.current_cursor = 0
        self.statuswin = curses.newwin(1,curses.COLS-1,curses.LINES-1,0)
        self.titlewin = curses.newwin(2,curses.COLS-1,0,0)
        self.start_inning=1

    # no navigation key support yet
    def Up(self):
        return
    
    def Down(self):
        return
    
    def PgUp(self):
        return

    def PgDown(self):
        return

    def Left(self):
        if self.start_inning - 9 < 1:
            self.start_inning = 1
        else:
            self.start_inning -= 9
        self.Refresh()

    def Right(self):
        last_inning = int(self.data['game']['inning'])
        # don't try to scroll past the end of the game
        if self.start_inning + 9 <= last_inning:
            self.start_inning += 9
        self.Refresh()

    def resize(self):
        self.statuswin.mvwin(curses.LINES-1,0)
        self.statuswin.resize(1,curses.COLS-1)
        self.titlewin.mvwin(0, 0)
        self.titlewin.resize(2,curses.COLS-1)
    
    def Refresh(self):
        if len(self.data) == 0:
            self.titlewin.refresh()
            self.myscr.refresh()
            self.statuswin.refresh()
            return

        self.myscr.clear()
        self.records = []
        self.prepareLineScoreFrames(self.start_inning)
        self.prepareActionLines()
        self.prepareInGameLine()
        self.prepareHrLine()
        n = 2
        for s in self.records:
            if n < curses.LINES-4:
                self.myscr.addnstr(n,0,s,curses.COLS-2)
            else:
                continue
            n+=1
        self.myscr.refresh()

    def titleRefresh(self,mysched):
        if len(self.data) == 0:
            titlestr = "NO LINE SCORE AVAILABLE FOR THIS GAME"
        else:
            (year,month,day) = self.data['game']['id'].split('/')[:3]
            titlestr = "LINE SCORE FOR  " +\
                self.data['game']['id'] +\
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

        # And write the status
        try:
            self.statuswin.addnstr(0,0,status_str,curses.COLS-2,curses.A_BOLD)
        except:
            rows = curses.LINES
            cols = curses.COLS
            slen = len(status_str)
            raise Exception,'(' + str(slen) + '/' + str(cols) + ',' + str(n) + '/' + str(rows) + ') ' + status_str
        self.statuswin.refresh()

    # adds the line score frames to self.records
    def prepareLineScoreFrames(self,start_inning=1):
        status = self.data['game']['status']
        if status in ( 'In Progress', ):
            status_str = "%s %s" % ( self.data['game']['inning_state'] ,
                                     self.data['game']['inning'] )
        elif status in ( 'Final', 'Game Over' , 'Completed Early' ):
            status_str = status
            if status == 'Completed Early' and self.data['game']['reason'] != "":
                status_str += ": %s" % self.data['game']['reason'] 
            # handle extra innings
            if self.data['game']['inning'] != '9':
                status_str += "/%s" % self.data['game']['inning']
        elif status in ( 'Delayed Start', 'Delayed', 'Postponed', 'Suspended' ):
            status_str = status
            if self.data['game']['reason'] != "":
                status_str += ": %s" % self.data['game']['reason'] 
            if self.data['game'].has_key('resume_date'):
                status_str += " (Completion on %s)" % self.data['game']['resume_date']
        else:
            status_str = status
        self.records.append(status_str)
        if self.data['game'].has_key('description'):
            self.records.append(self.data['game']['description'])
        # insert blank line before header row
        self.records.append("")
        
        # now for the frames - could fix it to 32 or leave it 'variable' for
        # now...
        team_strlen = 32
        team_sfmt = '%-' + '%s' % team_strlen + 's'

        # header string has inning numbers and R H E headers
        header_str = team_sfmt % ( ' '*team_strlen )
        # DONE: Extras are supported with Left/Right :)
        # extras
        end_inning=start_inning+9
        try:
            last_inning=int(self.data['game']['inning'])
        except:
            last_inning = 9
        for i in range(start_inning,end_inning):
            if i > last_inning:
                header_str += "%3s" % (' '*3)
            else:
                header_str += "%3s" % str(i)
        header_str += "%2s%3s%3s%3s" % ( "", "R", "H", "E" )
        self.records.append(header_str)
    
        # now to fill out the actual frames
        for team in ( 'away', 'home' ):
            if self.mycfg.get('milbtv'):
                team_str = TEAMCODES[self.data['game']['%s'%team+"_code"]][1]
            else:
                team_str = TEAMCODES[self.data['game']['%s'%team+"_file_code"]][1]
            team_str += " (%s-%s)" %\
                ( self.data['game']["%s_win"%team], 
                  self.data['game']["%s_loss"%team] )
            s = team_sfmt % team_str
            for inn in range(start_inning,end_inning):
                if self.data['innings'].has_key(str(inn)):
                    if self.data['innings'][str(inn)].has_key(team):
                        if self.data['innings'][str(inn)][team] == "" and \
                                                                   inn == 9:
                            if team == "home" and status in ('Game Over',
                                                             'Final' ):
                                # all of this just to fill in the bot 9 home win
                                    s+= "%3s" % "X"
                            else:
                                # not game over yet, print empty frame
                                s += "%3s" % (' '*3)
                        else:
                            s += "%3s" % self.data['innings'][str(inn)][team]
                    else:
                        s += "%3s" % (' '*3)
                else:
                    s += "%3s" % (' '*3)
            try:
                s += "%2s%3s%3s%3s" % ( " "*2, 
                                       self.data['game']["%s_team_runs"%team],
                                       self.data['game']["%s_team_hits"%team],
                                       self.data['game']["%s_team_errors"%team])
            except:
                s += '%2s%3s%3s%3s' % ( '', '0', '0', '0' )
            self.records.append(s)
        # insert a blank line before win/loss, currents, or probables
        self.records.append("")

    # this will contain:
    #     for in progress games, current pitcher, hitter, on base status, outs
    #         the count and eventually home runs
    #     for final and game over, display winning/losing/save pitchers, and 
    #         eventually home runs
    #     for future games, print the probable pitchers
    def prepareActionLines(self):
        status = self.data['game']['status']
        if status in ( 'In Progress', 'Delayed', 'Suspended' ):
            self.prepareActionInProgress()
        elif status in ( 'Final', 'Game Over', 'Completed Early' ):
            self.prepareActionFinal()
        elif status in ( 'Preview', 'Pre-Game', 'Warmup', 'Delayed Start' ):
            self.prepareActionPreview()
        elif status in ( 'Postponed', ):
            return
        else:
            raise Exception,status

    def prepareActionInProgress(self):
        status = self.data['game']['status']
        if self.data['game']['inning_state'] == 'Top':
            ( pteam, bteam ) = ( 'home', 'away' )
        else:
            ( pteam, bteam ) = ( 'away', 'home' )
        if status not in ( 'Suspended', ):
            if self.mycfg.get('milbtv'):
                s = "Pitching: %s (%s); Batting: %s (%s)" % \
                ( self.data['pitchers']['current_pitcher'][1],
                  self.data['game']["%s"%pteam+"_code"].upper(),
                  self.data['pitchers']['current_batter'][1],
                  self.data['game']["%s"%bteam+"_code"].upper() )
            else:
                s = "Pitching: %s (%s); Batting: %s (%s)" % \
                ( self.data['pitchers']['current_pitcher'][1],
                  self.data['game']["%s"%pteam+"_file_code"].upper(),
                  self.data['pitchers']['current_batter'][1],
                  self.data['game']["%s"%bteam+"_file_code"].upper() )
        try:
            # avoid a strange race condition encountered once
            # it is possible, status in linescore.xml was 'In Progress' but
            # game had just finished and miniscoreboard.xml no longer has
            # in_game information
            ondeck = self.data['in_game']['ondeck']['name_display_roster'] 
            ondeck_str = "; On deck: %s" % ondeck
            if len(s) + len(ondeck_str) < curses.COLS-2:
                s += ondeck_str
                self.records.append(s)
            else:
                self.records.append(s)
                self.records.append("On deck: %s" % ondeck)
        except:
            # it is also possible that the runner on base information below
            # might also be out of sync between linescore.xml and 
            # miniscoreboard.xml.  For such a rare race condition, we may want
            # to change this from pass to return...
            pass
        self.records.append("")
        #s = "Runners on base: " +\
        #    RUNNERS_ONBASE_STATUS[self.data['game']['runner_on_base_status']]
        if int(self.data['game']['runner_on_base_status']) > 0:
            self.records.append("Runners on base:")
            for base in ('runner_on_1b', 'runner_on_2b', 'runner_on_3b'):
                if self.data['in_game'][base]['id'] != "":
                    self.records.append("%s: %s" % \
                        ( RUNNERS_ONBASE_STRINGS[base], 
                          self.data['in_game'][base]['name_display_roster']))
        else:
            s = "Runners on base: None"
            self.records.append(s)
        self.records.append("")
        s = "%s-%s, %s outs" % \
            ( self.data['game']['balls'], self.data['game']['strikes'],
              self.data['game']['outs'] )
        self.records.append(s)

    def prepareActionFinal(self):
        wp_str = "W: %s (%s-%s %s)" %\
            ( self.data['pitchers']['winning_pitcher'][1],
              self.data['pitchers']['winning_pitcher'][2],
              self.data['pitchers']['winning_pitcher'][3],
              self.data['pitchers']['winning_pitcher'][4] )
        lp_str = "L: %s (%s-%s %s)" %\
            ( self.data['pitchers']['losing_pitcher'][1],
              self.data['pitchers']['losing_pitcher'][2],
              self.data['pitchers']['losing_pitcher'][3],
              self.data['pitchers']['losing_pitcher'][4] )
        s = "%-35s%-35s" % ( wp_str, lp_str )
        self.records.append(s)
        if self.data['pitchers']['save_pitcher'][0] != "":
            self.records.append("SV: %s (%s)" %\
                ( self.data['pitchers']['save_pitcher'][1],
                  self.data['pitchers']['save_pitcher'][5] ) )

    def prepareActionPreview(self):
        code = ('file_code','code')[self.mycfg.get('milbtv')]
        hp_str = '%3s: %s (%s-%s %s)' %\
            ( self.data['game']['home_%s'%code].upper(),
              self.data['pitchers']['home_probable_pitcher'][1],
              self.data['pitchers']['home_probable_pitcher'][2],
              self.data['pitchers']['home_probable_pitcher'][3],
              self.data['pitchers']['home_probable_pitcher'][4] )
        ap_str = '%3s: %s (%s-%s %s)' %\
            ( self.data['game']['away_%s'%code].upper(),
              self.data['pitchers']['away_probable_pitcher'][1],
              self.data['pitchers']['away_probable_pitcher'][2],
              self.data['pitchers']['away_probable_pitcher'][3],
              self.data['pitchers']['away_probable_pitcher'][4] )
        self.records.append("Probables: %s" % ap_str)
        self.records.append("%11s" % (' '*11) + hp_str)

    def prepareInGameLine(self):
        status = self.data['game']['status']
        if status not in ( 'In Progress', 'Suspended' ):
            return
        if not self.data.has_key('in_game'):
            return
        if self.data['in_game'].has_key('last_pbp'):
            s = "Last play: "
            # make sure line breaks at word boundary rather than wrapping
            for word in self.data['in_game']['last_pbp'].split(' '):
                if len(s) + len(word) < curses.COLS-2:
                    s += ' ' + word
                else:
                    self.records.append(s)
                    s = word
            self.records.append(s)

    def prepareHrLine(self):
        if not self.data.has_key('hr'):
            return
        if len(self.data['hr']) == 0:
            self.records.append("")
            self.records.append("HR: None")
            return
        if self.mycfg.get('milbtv'):
            ( away , home ) = ( self.data['game']['away_code'].upper(),
                                self.data['game']['home_code'].upper() )
        else:
            ( away , home ) = ( self.data['game']['away_file_code'].upper(),
                                self.data['game']['home_file_code'].upper() )
        # start with a blank line before
        self.records.append("")
        self.records.append("HR:")
        for team in ( away, home ):
            s = ""
            if not self.data['hr'].has_key(team):
                continue
            s += "%3s: " % team
            for player in self.data['hr'][team]:
                hr = len(self.data['hr'][team][player])
                if hr > 1:
                    try:
                        latest = self.data['hr'][team][player].keys()[-1]
                        hr_str = "%s %s (%s), " %\
                        ( self.data['hr'][team][player][latest][1],
                          str(hr),
                          self.data['hr'][team][player][latest][4] )
                    except:
                        raise Exception,repr(self.data['hr'][team][player])
                else:
                    hr_str = "%s (%s), " %\
                        ( self.data['hr'][team][player][hr][1],
                          self.data['hr'][team][player][hr][4] )
                if len(s) + len(hr_str) < curses.COLS-1:
                    s += hr_str
                else:
                    # start a new line
                    self.records.append(s)
                    s = hr_str
            self.records.append(s.strip(", "))


