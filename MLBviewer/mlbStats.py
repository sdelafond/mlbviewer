#!/usr/bin/env python

import json
import urllib2
import datetime
import httplib

from mlbError import *
from mlbConstants import *
from mlbHttp import MLBHttp

class MLBStats:

    def __init__(self,cfg=None):
        self.data = []
        self.mycfg = cfg
        self.last_update = ""
        self.date = datetime.datetime.now()
        self.season = self.date.year
        self.http = MLBHttp(accept_gzip=True)
        if self.mycfg is None:
            self.type = 'pitching'
            self.sort = 'era'
            self.league = 'MLB'
            self.sort_order = 'default'
            self.team = 0
            self.season = self.date.year
            self.player_pool = 'QUALIFIER'

    def prepareStatsUrl(self): 
        self.url = 'http://mlb.mlb.com/pubajax/wf/flow/stats.splayer?page_type=SortablePlayer&game_type=%27R%27&player_pool=QUALIFIER&sport_code=%27mlb%27&results=1000&recSP=1&recPP=50'
        self.league = self.mycfg.get('league')
        if self.league.upper() in ( 'NL' , 'AL' ):
            self.url += '&league_code=%%27%s%%27' % self.league.upper()
        self.type = self.mycfg.get('stat_type')
        self.sort = self.mycfg.get('sort_column')
        self.url += '&stat_type=%s&sort_column=%%27%s%%27' % (self.type,
                                                              self.sort)
        self.season_type = self.mycfg.get('season_type')
        if self.season_type == 'ANY':
            self.url += '&season=%s' %  self.mycfg.get('season')
        else:
            self.url += '&season='
        self.url += '&season_type=%s' % self.season_type
        self.sort_order = int(self.mycfg.get('sort_order'))
        if self.sort in ( 'era', 'whip', 'l' ) and self.sort_order == 0:
            self.url += '&sort_order=%27asc%27'
        elif self.sort_order == 0:
            self.url += '&sort_order=%27desc%27'
        else:
            self.url += '&sort_order=%%27%s%%27' % STATS_SORT_ORDER[int(self.sort_order)]
        self.team = self.mycfg.get('sort_team')
        if int(self.team) > 0:
            self.url += '&team_id=%s' % self.team
            self.url = self.url.replace('QUALIFIER','ALL')
        self.active_sw = int(self.mycfg.get('active_sw'))
        if self.active_sw:
            self.url += '&active_sw=%27Y%27'

    def prepareTripleCrownUrl(self):
        if self.type == 'pitching':
            self.url = 'http://mlb.mlb.com/lookup/json/named.leader_pitching_repeater.bam?results=5&season=2014&game_type=%27R%27&leader_pitching_repeater.col_in=era&leader_pitching_repeater.col_in=w&leader_pitching_repeater.col_in=so&leader_pitching_repeater.col_in=name_last&leader_pitching_repeater.col_in=team_abbrev&leader_pitching_repeater.col_in=player_id&sort_column=%27era%27&sort_column=%27w%27&sort_column=%27so%27&sport_code=%27mlb%27'
        else:
            self.url = 'http://mlb.mlb.com/lookup/json/named.leader_hitting_repeater.bam?results=5&season=2014&game_type=%27R%27&leader_hitting_repeater.col_in=avg&leader_hitting_repeater.col_in=hr&leader_hitting_repeater.col_in=rbi&leader_hitting_repeater.col_in=name_last&leader_hitting_repeater.col_in=team_abbrev&leader_hitting_repeater.col_in=player_id&sort_column=%27avg%27&sort_column=%27hr%27&sort_column=%27rbi%27&sport_code=%27mlb%27'

    def preparePlayerUrl(self):
        self.url = 'http://mlb.mlb.com/lookup/json/named.sport_%s_composed.bam?' % self.type
        self.url += 'game_type=%27R%27&sport_code=%27mlb%27&sport_code=%27aaa%27&sport_code=%27aax%27&sport_code=%27afa%27&sport_code=%27afx%27&sport_code=%27asx%27&sport_code=%27rok%27&sort_by=%27season_asc%27'
        self.url += '&sport_%s_composed.season=%s' % (self.date.year, self.type)
        self.url += '&player_id=%s' % self.player
        

    def getStatsData(self):
        #raise Exception,repr(self.mycfg.data)
        self.type = self.mycfg.get('stat_type')
        self.triple = int(self.mycfg.get('triple_crown'))
        self.player = int(self.mycfg.get('player_id'))
        if self.player > 0:
            self.preparePlayerUrl()
        elif self.triple:
            self.prepareTripleCrownUrl()
        else:
            self.prepareStatsUrl()
        try:
            rsp = self.http.getUrl(self.url)
        except urllib2.URLError:
            self.error_str = "UrlError: Could not retrieve statistics"
            raise MLBUrlError,self.url
        try:
            self.json = json.loads(rsp)
        except Exception,error:
            raise MLBUrlError,self.url
            #raise MLBJsonError,error
        if self.player > 0:
            self.data = self.parsePlayerStats()
        elif self.triple:
            self.parseTripleStats()
        else:
            self.data = self.parseStats()

    def parsePlayerStats(self):
        out = []
        if self.type == 'hitting':
            results = self.json['sport_hitting_composed']['sport_hitting_tm']
            try:
                totals = self.json['sport_hitting_composed']['sport_career_hitting']['queryResults']['row'][0]
            except KeyError:
                totals = self.json['sport_hitting_composed']['sport_career_hitting']['queryResults']['row']
            self.last_update = results['queryResults']['created']
        else:
            results = self.json['sport_pitching_composed']['sport_pitching_tm']
            try:
                totals = self.json['sport_pitching_composed']['sport_career_pitching']['queryResults']['row'][0]
            except KeyError:
                totals = self.json['sport_pitching_composed']['sport_career_pitching']['queryResults']['row']
            self.last_update = results['queryResults']['created']
        if results['queryResults']['totalSize'] == '1':
            # json doesn't make single row as list so tuple it for same effect
            results['queryResults']['row'] = ( results['queryResults']['row'], )
        for year in results['queryResults']['row']:
            # neat but confusing to have minors mixed in
            if year['sport_code'] == 'mlb':
                out.append(year)
        totals['season'] = 'Tot'
        totals['team_abbrev'] = 'MLB'
        totals['team_id'] = 0
        out.append(totals)
        return out

    def parseStats(self):
        out = []
        self.last_update = self.json['stats_sortable_player']['queryResults']['created'] + '-04:00'
        try:
            for player in self.json['stats_sortable_player']['queryResults']['row']:
                out.append(player)
        except KeyError:
            return out
        return out

    def parseTripleStats(self):
        out = []
