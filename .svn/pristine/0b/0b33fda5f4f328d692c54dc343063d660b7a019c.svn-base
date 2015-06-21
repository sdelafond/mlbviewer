#!/usr/bin/env

import urllib2
from HTMLParser import HTMLParser
from mlbConstants import *
from mlbListWin import MLBListWin
from mlbError import *
from mlbSchedule import gameTimeConvert
import datetime
import curses
from xml.dom.minidom import parse
from xml.dom.minidom import parseString
from mlbHttp import MLBHttp

class MLBRssWin(MLBListWin):

    def __init__(self,myscr,mycfg):
        self.myscr = myscr
        self.mycfg = mycfg
        self.statuswin = curses.newwin(1,curses.COLS-1,curses.LINES-1,0)
        self.titlewin = curses.newwin(2,curses.COLS-1,0,0)
        self.rssUrl = 'http://mlb.mlb.com/partnerxml/gen/news/rss/mlb.xml'
        self.milbRssUrl = 'http://www.milb.com/partnerxml/gen/news/rss/milb.xml'
        self.data = []
        self.records = []
        self.current_cursor = 0
        self.record_cursor = 0
        self.game_cursor = 0
        self.htmlParser = HTMLParser()
        self.http = MLBHttp(accept_gzip=True)

    def getFeedFromUser(self):
        feed = self.prompter(self.statuswin,'Enter teamcode of feed:')
        feed = feed.strip()
        if self.mycfg.get('milbtv') and feed == "" or feed == "milb":
            feed = "milb"
        elif feed == "" or feed == "mlb":
            feed = 'mlb'
        elif feed not in TEAMCODES.keys():
            self.statusWrite('Invalid teamcode: '+feed,wait=2)
            return
        self.statusWrite('Retrieving feed for %s...'%feed,wait=1)
        # in this case, overwrite rather than aggregate
        self.data = []
        self.getRssData(team=feed)

    def getRssData(self,team='mlb'):
        if self.mycfg.get('milbtv'):
            try:
                team = TEAMCODES[team][2]
            except:
                pass
            rssUrl = self.milbRssUrl.replace('milb.xml','%s.xml'%team)
        else:
            rssUrl = self.rssUrl.replace('mlb.xml','%s.xml'%team)
        try:
            rsp = self.http.getUrl(rssUrl)
        except:
            self.error_str = "UrlError: Could not retrieve RSS."
            self.statusWrite(self.error_str,wait=2)
            return
            #raise MLBUrlError
        try:
            xp = parseString(rsp)
        except:
            self.error_str = "XmlError: Could not parse RSS."
            raise MLBXmlError
        # append rather than overwrite to allow multiple feeds to be aggregated
        #self.data = []
        self.parseRssData(xp)
        # this is all just initialization ; setCursors should be called to
        # align with listings position
        self.game_cursor = 0
        self.current_cursor = 0
        self.record_cursor = 0
        viewable = curses.LINES-4
        if viewable % 2 > 0:
            viewable -= 1
        self.records = self.data[:viewable]

    def setCursors(self,current_cursor,record_cursor):
        self.game_cursor = current_cursor + record_cursor
        # scoreboard scrolls two lines at a time
        absolute_cursor = self.game_cursor * 2
        viewable = curses.LINES-4
        if viewable % 2 > 0:
            viewable -= 1
        # integer division will give us the correct top record position
        try:
            self.record_cursor = ( absolute_cursor / viewable ) * viewable
        except:
            raise MLBCursesError,"Screen too small."
        # and find the current position in the viewable screen
        self.current_cursor = absolute_cursor - self.record_cursor
        # and finally collect the viewable records
        self.records = self.data[self.record_cursor:self.record_cursor+viewable]

    def parseRssData(self,xptr):
        for item in xptr.getElementsByTagName('item'):
            title = item.getElementsByTagName('title')[0].childNodes[0].data
            link  = item.getElementsByTagName('link')[0].childNodes[0].data
            try:
                link  = self.htmlParser.unescape(link)
            except:
                raise Exception,repr(link)
            try:
                desc  = item.getElementsByTagName('description')[0].childNodes[0].data
            except IndexError:
                desc = ""
            self.data.append((title,link,desc))


    def Up(self):
        if self.current_cursor - 2 < 0 and self.record_cursor - 2 >= 0:
            viewable = curses.LINES-4
            if viewable % 2 > 0:
                viewable -= 1
            self.current_cursor = viewable-2
            #if self.current_cursor % 2 > 0:
            #    self.current_cursor -= 1
            if self.record_cursor - viewable < 0:
                self.record_cursor = 0
            else:
                self.record_cursor -= viewable
                #if self.record_cursor % 2 > 0:
                #    self.record_cursor -= 1
            self.records = self.data[self.record_cursor:self.record_cursor+viewable]
        elif self.current_cursor > 0:
            self.current_cursor -= 2

    def Down(self):
        viewable=curses.LINES-4
        if self.current_cursor + 2 >= len(self.records) and\
           ( self.record_cursor + self.current_cursor + 2 ) < len(self.data):
            self.record_cursor += self.current_cursor + 2
            self.current_cursor = 0
            if ( self.record_cursor + viewable ) % 2 > 0:
                self.records = self.data[self.record_cursor:self.record_cursor+curses.LINES-5]
            else:
                self.records = self.data[self.record_cursor:self.record_cursor+curses.LINES-4]
        # Elif not at bottom of window
        elif self.current_cursor + 2 < self.records  and\
             self.current_cursor + 2  < curses.LINES-4:
            if (self.current_cursor + 2 + self.record_cursor) < len(self.data):
                self.current_cursor += 2
        # Silent else do nothing at bottom of window and bottom of records


    def Refresh(self):

        self.myscr.clear()
        # display even number of lines since games will be two lines
        wlen = curses.LINES-4
        if wlen % 2 > 0:
            wlen -= 1
        for n in range(wlen):
            if n < len(self.records):
                cursesflags = 0
                game_cursor = ( n + self.record_cursor ) / 2
                ( title, link, desc ) = self.data[game_cursor]
                if n % 2 > 0:
                    # second line of the feed item, underline it for division
                    # between items
                    if len(desc) > curses.COLS-2:
                        s = desc[:curses.COLS-5]
                        s += '...'
                    else:
                        s = desc
                        pad = curses.COLS-2 - len(s)
                        s += ' '*pad
                    if n - 1 == self.current_cursor:
                        cursesflags |= curses.A_UNDERLINE|curses.A_REVERSE
                    else:
                        cursesflags = curses.A_UNDERLINE
                    self.myscr.addnstr(n+2,0,s,curses.COLS-2,cursesflags)
                else:
                    s = title
                    pad = curses.COLS - 2 - len(s)
                    if n == self.current_cursor:
                        cursesflags |= curses.A_REVERSE|curses.A_BOLD
                    else:
                        cursesflags = curses.A_BOLD
                    self.myscr.addstr(n+2,0,s,cursesflags)
                    # don't bold the pad or it results in an uneven looking
                    # highlight
                    cursesflags ^= curses.A_BOLD
                    self.myscr.addstr(n+2,len(s),' '*pad,cursesflags)
            else:
                s = ' '*(curses.COLS-1)
                self.myscr.addnstr(n+2,0,s,curses.COLS-2)
        self.myscr.refresh()
                
    def titleRefresh(self,mysched):
        self.titlewin.clear()
        # RSS is always today - there are no archives
        now = datetime.datetime.now()
        titlestr = "RSS FEED FOR " +\
                str(now.month) + '/' +\
                str(now.day) + '/' +\
                str(now.year)
                # TODO: '(Use arrow keys to change days)'

        padding = curses.COLS - (len(titlestr) + 6)
        titlestr += ' '*padding
        pos = curses.COLS - 6
        self.titlewin.addstr(0,0,titlestr)
        self.titlewin.addstr(0,pos,'H', curses.A_BOLD)
        self.titlewin.addstr(0,pos+1, 'elp')
        self.titlewin.hline(1, 0, curses.ACS_HLINE, curses.COLS-1)
        self.titlewin.refresh()

    def statusRefresh(self):
        game_cursor = ( self.current_cursor + self.record_cursor ) / 2
        # BEGIN curses debug code
        if self.mycfg.get('curses_debug'):
            wlen=curses.LINES-4
            if wlen % 2 > 0:
                wlen -= 1
            status_str = "game_cursor=%s, wlen=%s, current_cursor=%s, record_cursor=%s, len(records)=%s" %\
                      ( game_cursor, wlen, self.current_cursor, self.record_cursor, len(self.records) )
            self.statuswin.clear()
            self.statuswin.addnstr(0,0,status_str,curses.COLS-2,curses.A_BOLD)
            self.statuswin.refresh()
            return
        # END curses debug code
        # use the url for status now
        status_str = self.data[game_cursor][1][:curses.COLS-2]
        padding = curses.COLS - len(status_str)
        # shrink the status string to fit if it is too many chars wide for
        # screen
        if padding < 0:
            status_str=status_str[:padding]
        status_str += ' '*padding

        self.statuswin.addnstr(0,0,status_str,curses.COLS-2,curses.A_BOLD)
        self.statuswin.refresh()
