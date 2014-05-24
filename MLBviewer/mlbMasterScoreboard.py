#!/usr/bin/env python

from xml.dom.minidom import parse
from xml.dom.minidom import parseString
from xml.dom import *
from mlbError import *
from mlbHttp import MLBHttp
import urllib2
import datetime
import time

class MLBMasterScoreboard:

    def __init__(self,gameid):
        self.gameid = gameid
        self.gameid = self.gameid.replace('/','_')
        self.gameid = self.gameid.replace('-','_')
        ( year, month, day ) = self.gameid.split('_')[:3]
        league = self.gameid.split('_')[4][-3:]
        self.error_str = "Could not retrieve master_scoreboard.xml file"
        self.http = MLBHttp(accept_gzip=True)


    def getScoreboardData(self,gameid):
        self.scoreboard = []
        self.gameid = gameid
        self.gameid = self.gameid.replace('/','_')
        self.gameid = self.gameid.replace('-','_')
        ( year, month, day ) = self.gameid.split('_')[:3]
        league = self.gameid.split('_')[4][-3:]
        self.sbUrl = 'http://gdx.mlb.com/components/game/%s/year_%s/month_%s/day_%s/master_scoreboard.xml' % ( league, year, month, day )
        try: 
            rsp = self.http.getUrl(self.sbUrl)
        except urllib2.URLError:
            self.error_str = "Could not retrieve master_scoreboard.xml file"
            raise MLBUrlError, self.error_str
        try:
            xp = parseString(rsp)
        except:
            self.error_str = "Could not parse master_scoreboard.xml file"
            raise MLBXmlError, self.error_str
        # if we got this far, initialize the data structure
        for game in xp.getElementsByTagName('game'):
            tmp = dict()
            gid = game.getAttribute('id')
            tmp[gid] = dict()
            tmp[gid] = self.parseGameData(game)
            try:
                for media in game.getElementsByTagName('media'):
                    type = media.getAttribute('type')
                    if type == "game":
                        free = media.getAttribute('free')
                        tmp[gid]['free'] = (False,True)[free=="ALL"]
                if not tmp[gid].has_key('free'):
                    tmp[gid]['free'] = False
            except:
                tmp[gid]['free'] = False
            try:
                tmp[gid]['totals'] = self.parseLineScore(game)
            except:
                tmp['totals'] = None
            status = tmp[gid]['status']
            if status in ('Final', 'Game Over', 'Completed Early'):
                tmp[gid]['pitchers'] = self.parseWinLossPitchers(game)
            elif status in ( 'In Progress', 'Delayed', 'Suspended', 
                             'Manager Challenge', 'Replay' ):
                tmp[gid]['pitchers'] = self.parseCurrentPitchers(game)
            else:
                tmp[gid]['pitchers'] = self.parseProbablePitchers(game)
            if tmp[gid]['status'] in ( 'In Progress', 'Delayed', 'Suspended',
                                                 'Replay',
                                                 'Manager Challenge',
                                                 'Completed Early',
                                                 'Game Over',
                                                 'Final' ):
                tmp[gid]['hr'] = dict()
                tmp[gid]['hr'] = self.parseHrData(game)
                if tmp[gid]['status'] in ( 'In Progress', 'Delayed', 
                                           'Replay',
                                           'Manager Challenge',
                                           'Suspended' ):
                    tmp[gid]['in_game'] = dict()
                    tmp[gid]['in_game'] = self.parseInGameData(game)
            self.scoreboard.append(tmp)
        return self.scoreboard

        
    def parseInGameData(self,game):
        out = dict()

        for tag in ( 'pbp', 'batter', 'pitcher', 'opposing_pitcher', 'ondeck', 
                     'inhole', 'runners_on_base' ):
            out[tag] = dict()
            for node in game.getElementsByTagName(tag):
                for attr in node.attributes.keys():
                    out[tag][attr] = node.getAttribute(attr)
        return out
                    

    def parseHrData(self,game):
        out = dict()

        # codes are not the same in this file so translate
        teamcodes = dict()
        ( home_code , away_code ) = ( game.getAttribute('home_code'),
                                      game.getAttribute('away_code') )
        ( home_fcode , away_fcode ) = ( game.getAttribute('home_file_code'),
                                        game.getAttribute('away_file_code'))
        teamcodes[home_code] = home_fcode
        teamcodes[away_code] = away_fcode
        for node in game.getElementsByTagName('home_runs'):
            for player in node.getElementsByTagName('player'):
                # mlb.com lists each homerun separately so track game and
                # season totals
                tmp = dict()
                for attr in player.attributes.keys():
                    tmp[attr] = player.getAttribute(attr)
                # if we already have the player, this is more than one hr
                # this game
                team = teamcodes[tmp['team_code']].upper()
                if not out.has_key(team):
                    out[team] = dict()
                if out[team].has_key(tmp['id']):
                    game_hr += 1
                else:
                    game_hr = 1
                    out[team][tmp['id']] = dict()
                out[team][tmp['id']][game_hr] = ( tmp['id'], 
                                            tmp['name_display_roster'],
                                            teamcodes[tmp['team_code']],
                                            game_hr,
                                            tmp['std_hr'],    
                                            tmp['inning'],
                                            tmp['runners'] )
        return out
              
    def parseGameData(self,node):
        out = dict()
        
        for attr in node.attributes.keys():
            out[attr] = node.getAttribute(attr)
        for sptr in node.getElementsByTagName('status'):
            for attr in sptr.attributes.keys():
                out[attr] = sptr.getAttribute(attr)
        return out
        

    def parseLineScore(self,xp):
        out = dict()

        for tag in ('r', 'h', 'e'):
            out[tag] = dict()
            for team in ( 'away', 'home' ):
                out[tag][team] = dict()
                for tptr in xp.getElementsByTagName(tag):
                    out[tag][team] = tptr.getAttribute(team)
        return out
                    

    def parseWinLossPitchers(self,xp):
        out = dict()
    
        for pitcher in ( 'winning_pitcher' , 'losing_pitcher' , 'save_pitcher'):
            for p in xp.getElementsByTagName(pitcher):
                tmp = dict()
                for attr in p.attributes.keys():
                    tmp[attr] = p.getAttribute(attr)
                if pitcher == 'save_pitcher':
                    out[pitcher] = ( tmp['id'], tmp['name_display_roster'], 
                                     tmp['wins'], tmp['losses'], tmp['era'], 
                                     tmp['saves'] )
                else:
                    out[pitcher] = ( tmp['id'], tmp['name_display_roster'], 
                                     tmp['wins'], tmp['losses'], tmp['era'] )
        return out

    def parseProbablePitchers(self,xp):
        out = dict()
    
        for pitcher in ( 'home_probable_pitcher', 'away_probable_pitcher'):
            for p in xp.getElementsByTagName(pitcher):
                tmp = dict()
                for attr in p.attributes.keys():
                    tmp[attr] = p.getAttribute(attr)
                out[pitcher] = ( tmp['id'], tmp['name_display_roster'],
                                 tmp['wins'], tmp['losses'], tmp['era'] )
        return out

    def parseCurrentPitchers(self,xp):
        out = dict()
    
        for pitcher in ( 'pitcher', 'opposing_pitcher'):
            for p in xp.getElementsByTagName(pitcher):
                tmp = dict()
                for attr in p.attributes.keys():
                    tmp[attr] = p.getAttribute(attr)
                out[pitcher] = ( tmp['id'], tmp['name_display_roster'],
                                 tmp['wins'], tmp['losses'], tmp['era'] )
        for b in xp.getElementsByTagName('batter'):
            tmp = dict()
            for attr in b.attributes.keys():
                tmp[attr] = b.getAttribute(attr)
            out['batter'] = ( tmp['id'], tmp['name_display_roster'], 
                              tmp['avg'] )
        return out
