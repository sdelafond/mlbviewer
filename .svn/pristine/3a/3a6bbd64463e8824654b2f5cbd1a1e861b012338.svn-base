#!/usr/bin/env python


import urllib2, httplib
import StringIO
import gzip
import datetime
import json
import re
from xml.dom.minidom import parseString
from mlbConstants import STANDINGS_DIVISIONS
from mlbConstants import STANDINGS_JSON_DIVISIONS
from mlbError import *
from mlbHttp import MLBHttp

class MLBStandings:

    def __init__(self):
        self.data = []
        self.last_update = ""
        self.xml = ""
        self.date = datetime.datetime.now()
        self.url = 'https://erikberg.com/mlb/standings.xml'
        self.jUrl = 'http://mlb.mlb.com/lookup/json/named.standings_schedule_date.bam?&sit_code=%27h0%27&league_id=103&league_id=104&all_star_sw=%27N%27&version=2'
        self.http = MLBHttp(accept_gzip=True)

    #def getStandingsData(self,offline=False,datetime=None,format='json'):
    #    if format == 'xml':
    #        self.getStandingsXmlData(offline)
    #    else:
    #        self.getStandingsJsonData(offline)

    def getStandingsData(self,ymd_tuple=None,offline=False):
        # this part needs to be added dynamically
        #schedule_game_date.game_date=%272013/06/12%27&season=2013
        # if not given a datetime, calculate it
        self.data = []
        if ymd_tuple is not None:
            now = datetime.datetime(ymd_tuple[0],ymd_tuple[1],ymd_tuple[2])
        else:
            now=datetime.datetime.now()
        self.jUrl = 'http://mlb.mlb.com/lookup/json/named.standings_schedule_date.bam?&sit_code=%27h0%27&league_id=103&league_id=104&all_star_sw=%27N%27&version=2'
        self.jUrl += '&season=%s&schedule_game_date.game_date=%%27%s%%27' % \
                              ( now.year, now.strftime('%Y/%m/%d') )
        try:
            rsp = self.http.getUrl(self.jUrl)
        except urllib2.URLError:
            self.error_str = "UrlError: Could not retrieve standings."
            raise MLBUrlError
        try:
            self.json = json.loads(rsp)
        except ValueError:
            if re.search(r'Check back soon',rsp) is not None:
                #raise Exception,MLBJsonError
                return
            raise Exception,rsp
            raise Exception,self.jUrl
            raise Exception,MLBJsonError
        self.parseStandingsJson()

    def getDataFromFile(self):
        # For development purposes, let's parse from a file (activate web
        # code later)
        f = open('standings.xml')
        self.xml = f.read()
        f.close()

    def getStandingsXmlData(self,offline=False):
        # To limit test requests until permission has been obtained
        # from data provider
        if offline:
            try:
                self.getDataFromFile()
                self.parseStandingsXml()
            except:
                pass
            return
        request = urllib2.Request(self.url)
        request.add_header('Accept-encoding', 'gzip')
        request.add_header('User-agent', 'mlbviewer/2013sf3 https://sourceforge.net/projects/mlbviewer/   (straycat000@yahoo.com)')
        opener = urllib2.build_opener()
        try:
            f = opener.open(request)
        except urllib2.URLError:
            self.error_str = "UrlError: Could not retrieve standings."
            raise MLBUrlError
        compressedData = f.read()
        compressedStream = StringIO.StringIO(compressedData)
        gzipper = gzip.GzipFile(fileobj=compressedStream)
        self.xml = gzipper.read()
        self.parseStandingsXml()

    def parseStandingsJson(self):
        tmp = dict()
        self.last_update = self.json['standings_schedule_date']['standings_all_date_rptr']['standings_all_date'][0]['queryResults']['created'] + '-04:00'
        for league in self.json['standings_schedule_date']['standings_all_date_rptr']['standings_all_date']:
            if int(league['queryResults']['totalSize']) == 0:
                #raise Exception,self.jUrl
                return
            for div in STANDINGS_JSON_DIVISIONS.keys():
                if not tmp.has_key(div):
                    tmp[div] = []
                for team in league['queryResults']['row']:
                    if team['division_id'] == div:
                        tmp[div].append(team)
        for div in ( '201', '202', '200', '204', '205', '203' ):
            if len(tmp[div]) > 0:
                self.data.append( (STANDINGS_JSON_DIVISIONS[div],
                                   self.parseDivisionJsonData(tmp[div])) )

    def parseStandingsXml(self):
        xp = parseString(self.xml)
        for metadata in xp.getElementsByTagName('sports-metadata'):
            self.last_update = metadata.getAttribute('date-time')
        for standing in xp.getElementsByTagName('standing'):
            for div in standing.getElementsByTagName('sports-content-code'):
                type=div.getAttribute('code-type')
                if type == "division":
                    key = div.getAttribute('code-key')
                    division = STANDINGS_DIVISIONS[key] 
            self.data.append((division,self.parseDivisionData(standing)))

    def parseDivisionData(self,xp):
        out = []
        for tptr in xp.getElementsByTagName('team'):
            out.append(self.parseTeamData(tptr))
        return out

    def parseDivisionJsonData(self,division):
        out = []
        for team in division:
            out.append(self.parseTeamJsonData(team))
        return out

    def parseTeamJsonData(self,team):
        tmp = dict()
        tmp['first'] = team['team_short']
        tmp['file_code'] = team['file_code']
        tmp['G'] = int(team['w']) + int(team['l'])
        tmp['W'] = team['w']
        tmp['L'] = team['l']
        tmp['GB'] = team['gb']
        tmp['E'] = team['elim']
        tmp['WCGB'] = team['gb_wildcard']
        if tmp['WCGB'] == '':
            tmp['WCGB'] = '-'
        tmp['WP'] = team['pct']
        tmp['STRK'] = team['streak']
        tmp['RS'] = team['runs']
        tmp['RA'] = team['opp_runs']
        ( tmp['HW'], tmp['HL'] ) = team['home'].split('-')
        ( tmp['AW'], tmp['AL'] ) = team['away'].split('-')
        ( tmp['L10_W'], tmp['L10_L'] ) = team['last_ten'].split('-')
        return tmp

    def parseTeamData(self,tptr):
        tmp = dict()
        for name in tptr.getElementsByTagName('name'):
            tmp['first'] = name.getAttribute('first')
            tmp['last']  = name.getAttribute('last')
        for teamStats in tptr.getElementsByTagName('team-stats'):
            tmp['G'] = teamStats.getAttribute('events-played')
            tmp['GB'] = teamStats.getAttribute('games-back')
            for totals in teamStats.getElementsByTagName('outcome-totals'):
                scope = totals.getAttribute('alignment-scope')
                if scope == "events-all":
                    tmp['W'] = totals.getAttribute('wins')
                    tmp['L'] = totals.getAttribute('losses')
                    tmp['WP'] = totals.getAttribute('winning-percentage')
                    streak = totals.getAttribute('streak-type')
                    if streak == 'win':
                        tmp['STRK'] = 'W'
                    else:
                        tmp['STRK'] = 'L'
                    tmp['STRK'] += str(totals.getAttribute('streak-total'))
                    tmp['RS'] = totals.getAttribute('points-scored-for')
                    tmp['RA'] = totals.getAttribute('points-scored-against')
                elif scope == "events-home":
                    tmp['HW'] = totals.getAttribute('wins')
                    tmp['HL'] = totals.getAttribute('losses')
                elif scope == "events-away":
                    tmp['AW'] = totals.getAttribute('wins')
                    tmp['AL'] = totals.getAttribute('losses')
                elif scope == "":
                    scope = totals.getAttribute('duration-scope')
                    if scope == 'events-most-recent-5':
                        tmp['L5_W'] = totals.getAttribute('wins')
                        tmp['L5_L'] = totals.getAttribute('losses')
                    elif scope == 'events-most-recent-10':
                        tmp['L10_W'] = totals.getAttribute('wins')
                        tmp['L10_L'] = totals.getAttribute('losses')
        return tmp
                        
                    

                
