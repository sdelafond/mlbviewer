#!/usr/bin/env python

from mlbConstants import *
from mlbError import *

import json
import datetime
import urllib2
from xml.dom.minidom import parse

class MLBDailyVideos:

    def __init__(self,mycfg=None):
        self.cfg = mycfg
        self.baseUrl = 'http://wapc.mlb.com/ws/search/MediaSearchService?start=1&hitsPerPage=200&type=json&sort=desc&sort_type=date&mlbtax_key='
        self.rawData = dict()
        self.xmlList = dict()
        self.xmlMedia = dict()
        self.data = dict()
    
    def getJsonData(self,key='fastCast'):
        url = self.baseUrl + MLBCOM_VIDKEYS[key]
        txheaders={'Referer': 'http://mlb.mlb.com'}
        req = urllib2.Request(url=url,headers=txheaders,data=None)
        rsp = urllib2.urlopen(req)

        self.rawData[key] = json.loads(rsp.read())
        self.data[key] = []

    def parseJsonData(self,key='fastCast'):
        today = datetime.datetime.now()
        weekAgo = today - datetime.timedelta(7)
        for item in self.rawData[key]['mediaContent']:
            dateCreated = datetime.datetime.strptime(item['dateTimeCreated'].split('T')[0],'%Y-%m-%d')
            if dateCreated >= weekAgo:
                self.data[key].append(item)
            else:
                self.data[key].append(item)

    def getXmlList(self,key='fastCast'):
        self.getJsonData(key)
        try:
            self.parseJsonData(key)
        except:
            raise Exception,repr(self.rawData[key])
        self.xmlList[key] = []
        for item in self.data[key]:
            date=item['date_added']
            title=item['title']
            url=item['url']
            blurb=item['blurb']
            bigBlurb=item['bigBlurb']
            kicker=item['kicker']
            self.xmlList[key].append((title, kicker, blurb, date, url))
        return self.xmlList[key]

    def getXmlItemUrl(self,item,key='fastCast'):
        url = item[4]
        txheaders={'Referer': 'http://mlb.mlb.com'}
        req = urllib2.Request(url=url,headers=txheaders,data=None)
        rsp = urllib2.urlopen(req)
        xptr = parse(rsp)
        #key='mustC'
        return self.getXmlItemMedia(xptr,key)

    def getXmlItemMedia(self,xptr,key='fastCast'):
        self.xmlMedia[key] = []
        tmp = dict()
        for media in xptr.getElementsByTagName('media'):
            for url in media.getElementsByTagName('url'):
                scenario = url.getAttribute('playback_scenario')
                if scenario == 'FLASH_800K_640X360':
                    tmp['800'] = url.childNodes[0].data
                elif scenario == 'FLASH_1200K_640X360':
                    tmp['1200'] = url.childNodes[0].data
                elif scenario == 'FLASH_1800K_960X540':
                    tmp['1800'] = url.childNodes[0].data
        if self.cfg.get('speed') >= 1800 and tmp.has_key('1800'):
            self.xmlMedia[key].append(tmp['1800'])
        else:
            if tmp.has_key('1200'):
                self.xmlMedia[key].append(tmp['1200'])
            else:
                self.xmlMedia[key].append(tmp['800'])
        return self.xmlMedia[key]

    def testCode(self,key='fastCast'):
        key='mustC'
        #self.getJsonData(key)
        #self.parseJsonData(key)
        self.getXmlList(key)
        item=self.xmlList[key][1]
        url=self.getXmlItemUrl(item)
        #self.getXmlMedia(xp,key)
        return url
