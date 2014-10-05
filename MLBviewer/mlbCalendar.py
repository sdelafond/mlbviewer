import json
import urllib2
import datetime
import time
import calendar

from mlbError import *
from mlbConstants import *
from mlbHttp import MLBHttp


class MLBCalendar:

    def __init__(self):
        self.games = []
        self.calendar = []
        self.http = MLBHttp(accept_gzip=True)

    def getData(self,teamid,year=None,month=None):
        self.teamid = teamid
        self.url = 'http://mlb.com/gen/schedule/'
        self.url += STATS_TEAMS[self.teamid] + '/'
        if year is not None and month is not None:
            self.year = year
            self.month = month
        else:
            self.now = datetime.datetime.now()
            self.year = self.now.year
            self.month = self.now.month
        self.url += "%s_%s.json" % ( self.year, self.month )
        try: 
            rsp = self.http.getUrl(self.url)
        except urllib2.URLError:
            self.error_str = "UrlError: Could not retrieve calendar."
            raise MLBUrlError,self.url
        try:
            jp = json.loads(rsp)
        except:
            self.error_str = "JsonError: Could not parse calendar."
            raise MLBJsonError
        # if we got this far, initialize the data structure
        self.collectCalendar(jp)
        return self.games

    def collectCalendar(self,jp):
        self.games = []
        for game in jp:
            if game.has_key('game_id'):
                self.games.append(game)

    def calendarMonth(self):
        self.calendar = []
        # TODO: Parse game data
        # Step 1: step through all entries in self.cal and create searchable
        # indices
        tmp = dict()
        for game in self.games:
            # index based on gid in order to capture double-headers
            gid=game['game_id']
            ( year, month, day ) = gid.split('/')[:3]
            key="%s-%02d-%02d" % ( year, int(month), int(day) )
            if not tmp.has_key(key):
                tmp[key] = []
            tmp[key].append(game)
        # Step 2: fill in any off days with None so we have no gaps
        ( firstday, daysinmonth ) = calendar.monthrange(self.year, self.month)
        for d in range(daysinmonth):
            key='%s-%02d-%02d' % ( self.year, self.month, d+1 )
            if not tmp.has_key(key):
                tmp[key] = None
        # Step 3: front-fill any days before start of month if month starts
        # after Sunday
        # convert firstday from week begins with monday to week begins with
        # sunday
        firstDate = datetime.datetime(self.year, self.month, 1)
        days = (firstday + 1) % 7
        while days > 0:
            dif=datetime.timedelta(days)
            thisDate = firstDate - dif
            # For simplicity, fill in days from prior month with None.
            # In reality, those days may have games/scores but assume user
            # will scroll back for prior month games.
            self.calendar.append((thisDate, None))
            days-=1
        # Step 4: fill in the rest with the days of the month
        for d in range(daysinmonth):
            thisDate = datetime.datetime(self.year, self.month, d+1)
            key='%s-%02d-%02d' % ( self.year, self.month, d+1 )
            self.calendar.append((thisDate, tmp[key]))
        return self.calendar

