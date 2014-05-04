from xml.dom.minidom import parse
from xml.dom.minidom import parseString
from xml.dom import *
from mlbHttp import MLBHttp
import urllib2
import datetime
from mlbError import *

class MLBLineScore:

    def __init__(self,gameid):
        self.gameid = gameid
        self.gameid = self.gameid.replace('/','_')
        self.gameid = self.gameid.replace('-','_')
        ( year, month, day ) = self.gameid.split('_')[:3]
        self.league = self.gameid.split('_')[4][-3:]
        self.boxUrl = 'http://gdx.mlb.com/components/game/%s/year_%s/month_%s/day_%s/gid_%s/linescore.xml' % ( self.league, year, month, day, self.gameid )
        self.hrUrl = self.boxUrl.replace('linescore.xml','miniscoreboard.xml')
        self.linescore = None
        self.http = MLBHttp(accept_gzip=True)


    def getLineData(self,gameid):
        self.gameid = gameid
        self.gameid = self.gameid.replace('/','_')
        self.gameid = self.gameid.replace('-','_')
        ( year, month, day ) = self.gameid.split('_')[:3]
        self.league = self.gameid.split('_')[4][-3:]
        self.boxUrl = 'http://gdx.mlb.com/components/game/%s/year_%s/month_%s/day_%s/gid_%s/linescore.xml' % ( self.league, year, month, day, self.gameid )
        self.hrUrl = self.boxUrl.replace('linescore.xml','miniscoreboard.xml')
        self.linescore = None
        try: 
            rsp = self.http.getUrl(self.boxUrl)
        except urllib2.URLError:
            self.error_str = "UrlError: Could not retrieve linescore."
            raise MLBUrlError
        try:
            xp = parseString(rsp)
        except:
            self.error_str = "XmlError: Could not parse linescore."
            raise MLBXmlError
        # if we got this far, initialize the data structure
        self.linescore = dict()
        self.linescore['game'] = dict()
        self.linescore['innings'] = dict()
        self.linescore['pitchers'] = dict()
        self.linescore['game'] = self.parseGameData(xp)
        try:
            self.linescore['innings'] = self.parseLineScore(xp)
        except:
            self.linescore['innings'] = None
        status = self.linescore['game']['status']
        if status in ('Final', 'Game Over', 'Completed Early'):
            self.linescore['pitchers'] = self.parseWinLossPitchers(xp)
        elif status in ( 'In Progress', 'Delayed' ):
            self.linescore['pitchers'] = self.parseCurrentPitchers(xp)
        else:
            self.linescore['pitchers'] = self.parseProbablePitchers(xp)
        if self.linescore['game']['status'] in ( 'In Progress', 
                                                 'Delayed',
                                                 'Suspended',
                                                 'Completed Early',
                                                 'Game Over',
                                                 'Final' ):
            hrptr = self.getHrData() 
            self.linescore['hr'] = dict()
            self.linescore['hr'] = self.parseHrData(hrptr)
            if self.linescore['game']['status'] in ( 'In Progress', 'Delayed', 
                                                     'Suspended' ):
                self.linescore['in_game'] = dict()
                self.linescore['in_game'] = self.parseInGameData(hrptr)
        return self.linescore

    def getHrData(self):
        try: 
            rsp = self.http.getUrl(self.hrUrl)
        except:
            self.error_str = "UrlError: Could not retrieve home run data."
            raise MLBUrlError
        try:
            xp = parseString(rsp)
        except:
            self.error_str = "XmlError: Could not parse home run data."
            raise MLBXmlError
        # initialize the structure
        return xp
        
    def parseInGameData(self,xp):
        out = dict()

        for ingame in xp.getElementsByTagName('in_game'):
            out['last_pbp'] = ingame.getAttribute('last_pbp')
            for tag in ( 'batter', 'pitcher', 'opposing_pitcher', 'ondeck', 
                         'inhole', 'runner_on_1b', 'runner_on_2b', 
                         'runner_on_3b' ):
                out[tag] = dict()
                for node in ingame.getElementsByTagName(tag):
                    for attr in node.attributes.keys():
                        out[tag][attr] = node.getAttribute(attr)
        return out
                    

    def parseHrData(self,xp):
        out = dict()

        # codes are not the same in this file so translate
        for game in xp.getElementsByTagName('game'):
            teamcodes = dict()
            ( home_code , away_code ) = ( game.getAttribute('home_code'),
                                          game.getAttribute('away_code') )
            ( home_fcode , away_fcode ) = ( game.getAttribute('home_file_code'),
                                            game.getAttribute('away_file_code'))
            teamcodes[home_code] = home_fcode
            teamcodes[away_code] = away_fcode
        for node in xp.getElementsByTagName('home_runs'):
            for player in node.getElementsByTagName('player'):
                # mlb.com lists each homerun separately so track game and
                # season totals
                tmp = dict()
                for attr in player.attributes.keys():
                    tmp[attr] = player.getAttribute(attr)
                # if we already have the player, this is more than one hr
                # this game
                if self.league != 'mlb':
                    team = tmp['team_code'].upper()
                else:
                    team = teamcodes[tmp['team_code']].upper()
                if not out.has_key(team):
                    out[team] = dict()
                if out[team].has_key(tmp['id']):
                    # game_hr is local to this loop so look it up each time
                    game_hr = out[team][tmp['id']].keys()[-1]
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
              
    def parseGameData(self,xp):
        out = dict()
        
        for node in xp.getElementsByTagName('game'):
            for attr in node.attributes.keys():
                out[attr] = node.getAttribute(attr)
        return out
        

    def parseLineScore(self,xp):
        out = dict()

        for iptr in xp.getElementsByTagName('linescore'):
            inning = iptr.getAttribute('inning')
            out[inning] = dict()
            for team in ( 'home', 'away' ):
                out[inning][team] = iptr.getAttribute("%s_inning_runs"%team)
        return out
                    

    def parseWinLossPitchers(self,xp):
        out = dict()
    
        for pitcher in ( 'winning_pitcher' , 'losing_pitcher' , 'save_pitcher'):
            for p in xp.getElementsByTagName(pitcher):
                tmp = dict()
                for attr in p.attributes.keys():
                    tmp[attr] = p.getAttribute(attr)
                if pitcher == 'save_pitcher':
                    out[pitcher] = ( tmp['id'], tmp['last_name'], 
                                     tmp['wins'], tmp['losses'], tmp['era'], 
                                     tmp['saves'] )
                else:
                    out[pitcher] = ( tmp['id'], tmp['last_name'], 
                                     tmp['wins'], tmp['losses'], tmp['era'] )
        return out

    def parseProbablePitchers(self,xp):
        out = dict()
    
        for pitcher in ( 'home_probable_pitcher', 'away_probable_pitcher'):
            for p in xp.getElementsByTagName(pitcher):
                tmp = dict()
                for attr in p.attributes.keys():
                    tmp[attr] = p.getAttribute(attr)
                out[pitcher] = ( tmp['id'], tmp['last_name'],
                                 tmp['wins'], tmp['losses'], tmp['era'] )
        return out

    def parseCurrentPitchers(self,xp):
        out = dict()
    
        for pitcher in ( 'current_pitcher', 'opposing_pitcher'):
            for p in xp.getElementsByTagName(pitcher):
                tmp = dict()
                for attr in p.attributes.keys():
                    tmp[attr] = p.getAttribute(attr)
                out[pitcher] = ( tmp['id'], tmp['last_name'],
                                 tmp['wins'], tmp['losses'], tmp['era'] )
        for b in xp.getElementsByTagName('current_batter'):
            tmp = dict()
            for attr in b.attributes.keys():
                tmp[attr] = b.getAttribute(attr)
            out['current_batter'] = ( tmp['id'], tmp['last_name'], tmp['avg'] )
        return out
