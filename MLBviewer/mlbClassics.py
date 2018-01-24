#!/usr/bin/env python

# This is the data library for mlbclassics
# The GUI will import this library and use inherited subclasses of MLBListWin.
# First screen will show the 9 or so playlists available.
# Drill down to an individual playlist to see the games available.
# Play a single game using youtube-dl.
# Leverage the .mlb/config for preferred video_player.
# On the whole, the GUI will be much more similar to mlbvideos.py than 
# mlbviewer.py.

import sys
import time

try:
    import gdata
    import gdata.youtube
    import gdata.youtube.service
except:
    pass
    #print "Missing dependency: python-gdata required for mlbclassics"
    #sys.exit()

from operator import itemgetter

# Filter out the Japanese results
def only_roman_chars(s):
    try:
        s.encode("iso-8859-1")
        return True
    except UnicodeDecodeError:
        return False


class MLBClassics:
  
    def __init__(self,cfg):
        self.ytService = gdata.youtube.service.YouTubeService()
        self.data = []
        self.cfg = cfg

    def getFeed(self,feed='MLBClassics'):
        # Populate a catch-all for all uploads even those not in a playlist
        tmp = dict()
        uri = 'http://gdata.youtube.com/feeds/api/users/%s/uploads' % feed
        tmp['title'] = 'All Uploads by %s' % feed
        tmp['url'] = uri
        tmp['author'] = feed
        # set a special flag for the gui code
        tmp['all'] = True
        self.data.append(tmp)

        # now handle all the playlists
        feed = self.ytService.GetYouTubePlaylistFeed(username=feed)
        for playlist in feed.entry:
            self.data.append(self.getPlaylist(playlist))
        return self.data

    def getPlaylist(self,playlist):
        tmp = dict()
        tmp['title'] = playlist.title.text
        tmp['url'] = playlist.feed_link[0].href
        tmp['author'] = playlist.author[0].name.text
        return tmp

    def getPlaylistEntries(self,feedUrl):
        tmp = dict()
        tmp['entries'] = []
        feed = self.ytService.GetYouTubeVideoFeed(feedUrl)
        remaining=int(feed.total_results.text)
        while remaining > 0:
            if feed is None:
                break
            for entry in feed.entry:
                e = self.getEntry(entry)
                if e is not None:
                    tmp['entries'].append(e)
            remaining=int(feed.total_results.text)-len(feed.entry)
            feed=self.ytService.GetNext(feed)
        #sortedEntries=sorted(tmp['entries'], key=itemgetter('title'))
        sortKey = self.cfg.get('entry_sort')
        if sortKey == 'published':
            rev=True
        else:
            rev=False
        sortedEntries=sorted(tmp['entries'],key=itemgetter(sortKey),reverse=rev)
        tmp['entries']=sortedEntries
        return tmp

    def getEntry(self,entry):
        if not only_roman_chars(entry.title.text):
            return None
        tmp = dict()
        tmp['title'] = entry.title.text
        tmp['url'] = entry.media.player.url.split('&')[0]
        tmp['description'] = entry.media.description.text
        tmp['author'] = entry.author[0].name.text
        tmp['duration'] = time.strftime('%H:%M:%S',time.gmtime(int(entry.media.duration.seconds)))
        tmp['published'] = entry.published.text
        return tmp

