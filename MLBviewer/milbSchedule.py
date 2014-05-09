#!/usr/bin/env python

import datetime
import time
import urllib2
import cookielib
import re
import json

from mlbConstants import *
from mlbError import *
from mlbGameTime import MLBGameTime


class MiLBSchedule:

    def __init__(self,ymd_tuple=None,time_shift=None):
        if not ymd_tuple:
            now = datetime.datetime.now()
            dif = datetime.timedelta(1)
            # at least for the night-owls, let the day go until 9am the next
            # morning
            if now.hour < 9:
                now = now - dif
            ymd_tuple = ( now.year, now.month, now.day )
        ( year, month, day ) = ymd_tuple
        t = datetime.datetime( year, month, day )
        ( self.year, self.month, self.day ) = t.strftime('%Y/%m/%d').split('/')
        self.ymd_str = t.strftime('%Y%m%d')
        self.year = int(self.year)
        self.month = int(self.month)
        self.day = int(self.day)
        self.json = "http://www.milb.com/multimedia/grid_min.json/index.jsp?ymd=" + self.ymd_str
        self.shift = time_shift

    def __getSchedule(self):
        txheaders = {'User-agent' : USERAGENT }
        data = None
        req = urllib2.Request(self.json, data, txheaders)
        try:
            fp = urllib2.urlopen(req)
            return fp
        except urllib2.HTTPError:
            self.error_str = "UrlError: Could not retrieve listings."
            raise MLBUrlError

    def __scheduleFromJson(self):
        out = []
        gameinfo = dict()
        media = json.loads(self.__getSchedule().read())
        for game in media['data']['games']['game']:
            # TODO: For starters, ignore games without media, revisit this later
            if not game['game_media'].has_key('homebase'):
                continue
            id = game['id']
            gameinfo[id] = dict()
            for key in game.keys():
                gameinfo[id][key] = game[key]
            event_time = game['event_time']
            listdate=datetime.datetime.strptime('%s %s' %\
                                                   ( event_time,self.ymd_str ),
                                                   '%I:%M %p %Y%m%d')
            gametime=MLBGameTime(listdate,self.shift)
            localdate = gametime.localize()
            gameinfo[id]['local_datetime'] = localdate
            gameinfo[id]['event_time'] = localdate
            gameinfo[id]['local_time'] = localdate.strftime('%I:%M %p')
            # retaining all the old data elements until proven unnecessary
            #gameinfo[id]['time'] = game['event_time'].split()[0]
            #gameinfo[id]['ampm'] = game['event_time'].split()[1]
            home = game['home_team_id']
            away = game['away_team_id']
            if game['game_media'].has_key('homebase'):
                gameinfo[id]['content'] = self.parseMediaGrid(game['game_media']['homebase']['media'],home,away)
            else:
                gameinfo[id]['content'] = []
            # update TEAMCODES dynamically
            for team in ( 'home' , 'away' ):
                teamcode=str(game['%s_code'%team])
                teamfilecode = str(game['%s_file_code'%team])
                if not TEAMCODES.has_key(teamcode):
                    TEAMCODES[teamcode] = ( str(game['%s_team_id'%team]),
                                '%s %s' % ( str(game['%s_team_city'%team]),
                                            str(game['%s_team_name'%team])),
                                            teamfilecode )
            out.append(gameinfo[id])
        return out
        
        
    def parseMediaGrid(self,gamemedia,home,away):
        content = {}
        content['audio'] = []
        content['video'] = {}
        content['video']['milbtv'] = []
        for media in gamemedia:
            event_id = ''
            display = media['display']
            content_id = media['id']
            scenario = media['playback_scenario']
            if scenario == 'FLASH_1000K_640X360':
                content['video']['milbtv'].append((display, home, content_id, event_id))
                content['video']['milbtv'].append((display, away, content_id, event_id))
        return content

    def getData(self):
        try:
            self.data = self.__scheduleFromJson()
        except ValueError,detail:
            self.error_str = repr(detail)
            raise MLBJsonError,detail

    def trimList(self):
        if not self.data:
            self.error_str = "No games available today"
            raise MLBXmlError,"No games available today."
        out = []
        for game in self.data:
            dct = {}
            dct['home'] = game['home_code']
            dct['away'] = game['away_code']
            dct['teams'] = {}
            dct['teams']['home'] = dct['home']
            dct['teams']['away'] = dct['away']
            dct['event_id'] = game['calendar_event_id']
            if dct['event_id'] == "":
                dct['event_id'] = None
            dct['ind'] = game['ind']
            try:
                dct['status'] = STATUSCODES[game['status']]
            except:
                dct['status'] = game['status']
            dct['gameid'] = game['id']
            dct['event_time'] = game['event_time']
            dct['video'] = {}
            dct['video']['milbtv'] = game['content']['video']['milbtv']
            dct['audio'] = []
            dct['condensed'] = None
            dct['media_state'] = game['game_media']['homebase']['media'][0]['combined_media_state'].lower()
            out.append((dct['gameid'], dct))
        return out

    def getListings(self,speed,blackout):
        self.getData()
        listings = self.trimList()
        
        return [(elem[1]['teams'],\
                     elem[1]['event_time'],
                     elem[1]['video']['milbtv'],
                     elem[1]['audio'],
                     elem[1]['condensed'],
                     elem[1]['status'],
                     elem[0],
                     elem[1]['media_state'])\
                         for elem in listings]

    def getPreferred(self,available,cfg):
        prefer = {}
        media  = {}
        media['video'] = {}
        media['audio'] = {}
        home = available[0]['home']
        away = available[0]['away']
        homecode = TEAMCODES[home][0]
        awaycode = TEAMCODES[away][0]
        # build dictionary for home and away video
        for elem in available[2]:
            if homecode and homecode in elem[1]:
                media['video']['home'] = elem
            elif awaycode and awaycode in elem[1]:
                media['video']['away'] = elem
            else:
                # handle game of the week
                media['video']['home'] = elem
                media['video']['away'] = elem
        # same for audio
        for elem in available[3]:
            if homecode and homecode in elem[1]:
                media['audio']['home'] = elem
            elif awaycode and awaycode in elem[1]:
                media['audio']['away'] = elem
            else:
                # handle game of the week
                media['audio']['home'] = elem
                media['audio']['away'] = elem
        # now build dictionary based on coverage and follow settings
        for type in ('audio' , 'video'):
            follow='%s_follow'%type
            # if home is in follow and stream available, use it, elif away, else
            # None
            if home in cfg.get(follow):
                try:
                    prefer[type] = media[type]['home']
                except:
                    if media[type].has_key('away'):
                        prefer[type] = media[type]['away']
                    else:
                        prefer[type] = None
            # same logic reversed for away in follow
            elif away in cfg.get(follow):
                try:
                    prefer[type] = media[type]['away']
                except:
                    try:
                        prefer[type] = media[type]['home']
                    except:
                        prefer[type] = None
            # if home or away not in follow, prefer coverage, if present, then
            # try first available, else None
            else:
                try:
                    prefer[type] = media[type][cfg.get('coverage')]
                except:
                    try:
                        if type == 'video':
                            prefer[type] = available[2][0]
                        else:
                            prefer[type] = available[3][0]
                    except:
                        prefer[type] = None
        return prefer

    def Back(self, myspeed, blackout):
        t = datetime.datetime(int(self.year), int(self.month), int(self.day))
        dif = datetime.timedelta(1)
        t -= dif
        ( self.year, self.month, self.day ) = t.strftime('%Y/%m/%d').split('/')
        self.ymd_tuple = ( self.year, self.month, self.day )
        self.ymd_str = '%s%s%s' % self.ymd_tuple 
        self.year = int(self.year)
        self.month = int(self.month)
        self.day = int(self.day)
        self.json = "http://www.milb.com/multimedia/grid_min.json/index.jsp?ymd=" + self.ymd_str
        return self.getListings(myspeed,blackout)

    def Forward(self, myspeed, blackout):
        t = datetime.datetime(int(self.year), int(self.month), int(self.day))
        dif = datetime.timedelta(1)
        t += dif
        ( self.year, self.month, self.day ) = t.strftime('%Y/%m/%d').split('/')
        self.ymd_tuple = ( self.year, self.month, self.day )
        self.ymd_str = '%s%s%s' % self.ymd_tuple 
        self.year = int(self.year)
        self.month = int(self.month)
        self.day = int(self.day)
        self.json = "http://www.milb.com/multimedia/grid_min.json/index.jsp?ymd=" + self.ymd_str
        return self.getListings(myspeed,blackout)

    def Jump(self, ymd_tuple, myspeed, blackout):
        t = datetime.datetime( ymd_tuple[0], ymd_tuple[1], ymd_tuple[2] )
        ( self.year, self.month, self.day ) = t.strftime('%Y/%m/%d').split('/')
        self.ymd_tuple = ( self.year, self.month, self.day )
        self.ymd_str = '%s%s%s' % self.ymd_tuple 
        self.year = int(self.year)
        self.month = int(self.month)
        self.day = int(self.day)
        self.json = "http://www.milb.com/multimedia/grid_min.json/index.jsp?ymd=" + self.ymd_str
        return self.getListings(myspeed, blackout)

