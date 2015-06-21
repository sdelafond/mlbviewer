from xml.dom.minidom import parse
from xml.dom.minidom import parseString
from xml.dom import *
from mlbHttp import MLBHttp
import urllib2
import datetime
from mlbError import *

class MLBBoxScore:

    def __init__(self,gameid):
        self.gameid = gameid
        self.gameid = self.gameid.replace('/','_')
        self.gameid = self.gameid.replace('-','_')
        ( year, month, day ) = self.gameid.split('_')[:3]
        league = self.gameid.split('_')[4][-3:]
        self.boxUrl = 'http://gdx.mlb.com/components/game/%s/year_%s/month_%s/day_%s/gid_%s/boxscore.xml' % ( league, year, month, day, self.gameid )
        self.boxscore = None
        self.http = MLBHttp(accept_gzip=True)


    def getBoxData(self,gameid):
        self.gameid = gameid
        self.gameid = self.gameid.replace('/','_')
        self.gameid = self.gameid.replace('-','_')
        ( year, month, day ) = self.gameid.split('_')[:3]
        league = self.gameid.split('_')[4][-3:]
        self.boxUrl = 'http://gdx.mlb.com/components/game/%s/year_%s/month_%s/day_%s/gid_%s/boxscore.xml' % ( league, year, month, day, self.gameid )
        self.boxscore = None
        try: 
            rsp = self.http.getUrl(self.boxUrl)
        except urllib2.URLError:
            self.error_str = "UrlError: Could not retrieve box score."
            raise MLBUrlError
        try:
            xp = parseString(rsp)
        except:
            raise
        # if we got this far, initialize the data structure
        self.boxscore = dict()
        self.boxscore['game'] = self.parseGameData(xp)
        self.boxscore['batting'] = self.parseBattingData(xp)
        self.boxscore['pitching'] = self.parsePitchingData(xp)
        self.boxscore['game_info'] = self.parseGameInfo(xp)
        return self.boxscore

    def parseGameData(self,xp):
        out = dict()
        
        for node in xp.getElementsByTagName('boxscore'):
            for attr in node.attributes.keys():
                out[attr] = node.getAttribute(attr)
        return out
        
    def parseBattingData(self,xp):
        out = dict()

        for node in xp.getElementsByTagName('batting'):
            team=node.getAttribute('team_flag')
            out[team] = dict()
            for attr in node.attributes.keys():
                out[team][attr] = node.getAttribute(attr)
            out[team]['batters'] = dict()
            for b in node.getElementsByTagName('batter'):
                b_id = b.getAttribute('id')
                out[team]['batters'][b_id] = dict()
                for a in b.attributes.keys():
                    out[team]['batters'][b_id][a] = b.getAttribute(a)
            # <note> tag contains substitution notes
            out[team]['batting-note'] = []
            for span in node.getElementsByTagName('note'):
                # encapsulate span data in foo tag and then parse it as 
                # well-behaved XML
                new='<foo>'+span.childNodes[0].data+'</foo>'
                tmp=parseString(new)
                for text in tmp.getElementsByTagName('span'):
                    # wait! really? span inside span???
                    out[team]['batting-note'].append(text.childNodes[0].data)
            # text_data is used for BATTING / FIELDING notes
            out[team]['batting-data'] = []
            # deal with culturing the messy blob later
            for blob in node.getElementsByTagName('text_data'):
                out[team]['batting-data'].append(blob)
        # good enough for here - do more parsing elsewhere
        return out
            
    def parsePitchingData(self,xp):
        out = dict()

        for node in xp.getElementsByTagName('pitching'):
            team=node.getAttribute('team_flag')
            out[team] = dict()
            for attr in node.attributes.keys():
                out[team][attr] = node.getAttribute(attr)
            out[team]['pitchers'] = dict()
            out[team]['pitchers']['pitching-order'] = list()
            for p in node.getElementsByTagName('pitcher'):
                p_id = p.getAttribute('id')
                out[team]['pitchers']['pitching-order'].append(p_id)
                out[team]['pitchers'][p_id] = dict()
                for a in p.attributes.keys():
                    out[team]['pitchers'][p_id][a] = p.getAttribute(a)
            # <note> tag contains substitution notes
            out[team]['pitching-note'] = []
            for span in node.getElementsByTagName('note'):
                tmp=parseString(span.childNodes[0].data) 
                for text in tmp.getElementsByTagName('span'):
                    out[team]['pitching-note'].append(text.childNodes[0].data)
            # text_data is used for additional notes
            out[team]['pitching-data'] = []
            for blob in node.getElementsByTagName('text_data'):
                out[team]['pitching-data'].append(blob)
        # good enough for here - do more parsing elsewhere
        return out

    # probably don't need this anymore since line score is another class
    def parseLineScore(self,xp):
        out = dict()

        for node in xp.getElementsByTagName('linescore'):
            out['totals'] = dict()
            for attr in node.attributes.keys():
                out['totals'][attr] = node.getAttribute(attr)
            out['innings'] = dict()
            for iptr in node.getElementsByTagName('inning_line_score'):
                inning = iptr.getAttribute('inning')
                out['innings'][inning] = dict()
                for team in ( 'home', 'away' ):
                    out['innings'][inning][team] = iptr.getAttribute(team)
        return out
                    
    def parseGameInfo(self,xp):
        for node in xp.getElementsByTagName('game_info'):
            # there should only be one
            return node

    def parseDataBlob(self,blob):
        data='<data>'+blob.childNodes[0].nodeValue + '</data>'
        dptr=parseString(data)
        out=[]
        tmp_str=''
        #print "dptr.childNodes[0].childNodes:"
        #print dptr.childNodes[0].childNodes
        for elem in dptr.childNodes[0].childNodes:
            self.blobNode(elem)

    def blobNode(self,node):
        if node.nodeName == 'b':
            print node.childNodes[0].nodeValue
        elif node.nodeName == 'span':
            for child in node.childNodes:
                self.blobNode(child)
        elif node.nodeType == node.TEXT_NODE:
            self.blobTextNode(node)
        elif node.nodeName == 'br':
            pass

    def blobTextNode(self,node):
        if not node.nodeValue.isspace():
            print node.nodeValue
            


if __name__ == "__main__":
    gameid = '2015/04/20/minmlb-kcamlb-1'
    Box = MLBBoxScore(gameid)
    boxscore = Box.getBoxData(gameid)
    Box.parseDataBlob(boxscore['batting']['home']['batting-data'][0])
