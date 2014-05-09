#!/usr/bin/env python

import datetime

from mlbGameTime import MLBGameTime
from mlbConstants import *

STATUSTEXT = {
    "CG" :	"Final",
    "P"  :	"Preview",
    "GO" : 	"Game Over",
    "E"  :	"Final",
    "I"  :	"Live",
    "W"  :      "Game Over",
    "F"  :	"Final",
    "S"  :	"Suspended",
    "D"  :	"Delayed",
    "IP" :	"Pregame",
    "PO" :	"Postponed",
    "NB" :	"Blackout",
    "LB" :	"Blackout",
}


class MLBMediaDetail:

    def __init__(self,mycfg,listings):
        self.listings = listings
        self.mycfg = mycfg

        # initialize some data structures
        self.games = []


    def parseListings(self):
        self.games = []
        for game in self.listings:
            gamedata=dict()
            gamedata['media'] = dict()
            gamedata['media']['audio'] = dict()
            gamedata['media']['alt_audio'] = dict()
            gamedata['media']['video'] = dict()
            gamedata['prefer'] = dict()

            gamedata['home']=game[0]['home']
            gamedata['away']=game[0]['away']
            gamedata['starttime']=game[1]
            try:
                ( gamedata['media']['video']['home'], \
                  gamedata['media']['video']['away'] ) = game[2]
            except:
                if len(game[2]) == 1:
                    try:
                        team = STATS_TEAMS[int(game[2][0][1])]
                    except:
                        raise Exception,repr(game[2][0])
                    gamedata['media']['video']['home'] = \
                        (("(None)",),game[2][0])[(team==gamedata['home'])]
                    gamedata['media']['video']['away'] = \
                        (("(None)",),game[2][0])[(team==gamedata['away'])]
                    if game[2][0][1] == '0':
                        gamedata['media']['video']['home'] = game[2][0]
                        gamedata['media']['video']['away'] = ("(None)",)
                    #gamedata['media']['video']['home'] = game[2][0]
                    #gamedata['media']['video']['away'] = game[2][0]
            try:
                ( gamedata['media']['audio']['home'],  \
                  gamedata['media']['audio']['away'] ) = game[3]
            except:
                if len(game[3]) == 1:
                    try:
                        team = STATS_TEAMS[int(game[3][0][1])]
                    except:
                        raise Exception,repr(game[3][0])
                    gamedata['media']['audio']['home'] = \
                        (("(None)",),game[3][0])[(team==gamedata['home'])]
                    gamedata['media']['audio']['away'] = \
                        (("(None)",),game[3][0])[(team==gamedata['away'])]
                    if game[3][0][1] == '0':
                        gamedata['media']['audio']['home'] = game[3][0]
                        gamedata['media']['audio']['away'] = ("(None)",)
            gamedata['media']['condensed'] = game[4]
            gamedata['status'] = STATUSTEXT.get(game[5])
            gamedata['statustext'] = STATUSLINE.get(game[5],"Unknown flag: " +\
                                        game[5] )
            gamedata['gameid'] = game[6]
            gamedata['archive'] = (0,1)[(game[7] == "media_archive")]
            gamedata['mediastart'] = game[8]
            gamedata['free'] = game[9]
            for alt in game[10]:
                if len(alt):
                    team = STATS_TEAMS[int(alt[1])]
                else:
                    team = None
                for k in ( 'away', 'home' ):
                    if team == gamedata[k]:
                        gamedata['media']['alt_audio'][k] = alt
            for k in ( 'away', 'home' ):
                if not gamedata['media']['alt_audio'].has_key(k):
                    gamedata['media']['alt_audio'][k] = []
            self.games.append(gamedata)
        return self.games

