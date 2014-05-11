#!/usr/bin/env python

# mlbviewer is free software; you can redistribute it and/or modify
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, Version 2.
#
# mlbviewer is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# For a copy of the GNU General Public License, write to the Free
# Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# 02111-1307 USA

VERSION ="2014-sf-2"
URL = "http://sourceforge.net/projects/mlbviewer"
EMAIL = "straycat000@yahoo.com"

import os
import subprocess
import select
from copy import deepcopy
import sys
import curses
#from __init__ import VERSION, URL
from mlbDefaultKeyBindings import DEFAULT_KEYBINDINGS
from mlbStatsKeyBindings import STATS_KEYBINDINGS

# Set this to True if you want to see all the html pages in the logfile
SESSION_DEBUG=True
#DEBUG = True
#DEBUG = None
#from __init__ import AUTHDIR

# Change this line if you want to use flvstreamer instead
DEFAULT_F_RECORD = 'rtmpdump -f \"LNX 10,0,22,87\" -o %f -r %s'

# Change the next two settings to tweak mlbhd behavior
DEFAULT_HD_PLAYER = 'mlbhls -B %B'
HD_ARCHIVE_OFFSET = '48'

AUTHDIR = '.mlb'
COOKIEFILE = os.path.join(os.environ['HOME'], AUTHDIR, 'cookie')
SESSIONKEY = os.path.join(os.environ['HOME'], AUTHDIR, 'sessionkey')
LOGFILE = os.path.join(os.environ['HOME'], AUTHDIR, 'log')
ERRORLOG_1 = os.path.join(os.environ['HOME'], AUTHDIR, 'unsuccessful-1.xml')
ERRORLOG_2 = os.path.join(os.environ['HOME'], AUTHDIR, 'unsuccessful-2.xml')
MEDIALOG_1 = os.path.join(os.environ['HOME'], AUTHDIR, 'successful-1.xml')
MEDIALOG_2 = os.path.join(os.environ['HOME'], AUTHDIR, 'successful-2.xml')
FMSLOG     = os.path.join(os.environ['HOME'], AUTHDIR, 'fmscloud.xml')
SESSIONLOG = os.path.join(os.environ['HOME'], AUTHDIR, 'session.xml')
USERAGENT = 'Mozilla/5.0 (Windows NT 5.1; rv:18.0) Gecko/20100101 Firefox/18.0'
TESTXML = os.path.join(os.environ['HOME'], AUTHDIR, 'test_epg.xml')
BLACKFILE = os.path.join(os.environ['HOME'], AUTHDIR, 'blackout.xml')
HIGHLIGHTS_LIST = '/tmp/highlights.m3u8'

SOAPCODES = {
    "1"    : "OK",
    "-1000": "Requested Media Not Found",
    "-1500": "Other Undocumented Error",
    "-1600": "Requested Media Not Available Yet.",
    "-2000": "Authentication Error",
    "-2500": "Blackout Error",
    "-3000": "Identity Error",
    "-3500": "Sign-on Restriction Error",
    "-4000": "System Error",
}

# Status codes: Reverse mapping of status strings back to the status codes
# that were used in the json days.  Oh, those were the days. ;-)
STATUSCODES = {
    "In Progress"     : "I",
    "Completed Early" : "E",
    "Cancelled"       : "C",
    "Final"           : "F",
    "Preview"         : "P",
    "Postponed"       : "PO",
    "Game Over"       : "GO",
    "Delayed Start"   : "D",
    "Delayed"         : "D",
    "Pre-Game"        : "IP",
    "Suspended"       : "S",
    "Warmup"          : "IP",
}



# We've never used the first field, so I'm going to expand its use for 
# audio and video follow functionality.  The first field will contain a tuple
# of call letters for the various media outlets that cover that team.
TEAMCODES = {
    'ana': ('108', 'Los Angeles Angels'),
    'al' : ( None, 'American League', ''),
    'ari': ('109', 'Arizona Diamondbacks', ''),
    'atl': ('144', 'Atlanta Braves', ''),
    'bal': ('110', 'Baltimore Orioles',''),
    'bos': ('111', 'Boston Red Sox', ''),
    'chc': ('112', 'Chicago Cubs', ''),
    'chn': ('112', 'Chicago Cubs', ''),
    'cin': ('113', 'Cincinnati Reds', ''),
    'cle': ('114', 'Cleveland Indians', ''),
    'col': ('115', 'Colorado Rockies', ''),
    'cws': ('145', 'Chicago White Sox', ''),
    'cha': ('145', 'Chicago White Sox', ''),
    'det': ('116', 'Detroit Tigers', ''),
    'fla': ('146', 'Florida Marlins', ''),
    'flo': ('146', 'Florida Marlins', ''),
    'mia': ('146', 'Miami Marlins', ''),
    'hou': ('117', 'Houston Astros', ''),
    'kc':  ('118', 'Kansas City Royals', ''),
    'kca': ('118', 'Kansas City Royals', ''),
    'la':  ('119', 'Los Angeles Dodgers', ''),
    'lan':  ('119', 'Los Angeles Dodgers', ''),
    'mil': ('158', 'Milwaukee Brewers', ''),
    'min': ('142', 'Minnesota Twins', ''),
    'nl' : ( None, 'National League', ''),
    'nym': ('121', 'New York Mets', ''),
    'nyn': ('121', 'New York Mets', ''),
    'nyy': ('147', 'New York Yankees', ''),
    'nya': ('147', 'New York Yankees', ''),
    'oak': ('133', 'Oakland Athletics', ''),
    'phi': ('143', 'Philadelphia Phillies', ''),
    'pit': ('134', 'Pittsburgh Pirates', ''),
    'sd':  ('135', 'San Diego Padres', ''),
    'sdn': ('135', 'San Diego Padres', ''),
    'sea': ('136', 'Seattle Mariners', ''),
    'sf':  ('137', 'San Francisco Giants', ''),
    'sfn': ('137', 'San Francisco Giants', ''),
    'stl': ('138', 'St. Louis Cardinals', ''),
    'sln': ('138', 'St. Louis Cardinals', ''),
    'tb':  ('139', 'Tampa Bay Rays', ''),
    'tba': ('139', 'Tampa Bay Rays', ''),
    'tex': ('140', 'Texas Rangers', ''),
    'tor': ('141', 'Toronto Blue Jays', ''),
    'was': ('120', 'Washington Nationals', ''),
    'wft': ('WFT', 'World Futures Team' ),
    'uft': ('UFT', 'USA Futures Team' ),
    'cif': ('CIF', 'Cincinnati Futures Team'),
    'nyf': ('NYF', 'New York Yankees Futures Team'),
    't3944': ( 'T3944', 'CPBL All-Stars' ),
    'unk': ( None, 'Unknown', 'Teamcode'),
    'tbd': ( None, 'TBD'),
    't102': ('T102', 'Round Rock Express'),
    't103': ('T103', 'Lake Elsinore Storm'),
    't234': ('T234', 'Durham Bulls'),
    't235': ('T235', 'Memphis Redbirds'),
    't241': ('T241', 'Yomiuri Giants (Japan)'),
    't249': ('T249', 'Carolina Mudcats'),
    't260': ('T260', 'Tulsa Drillers'),
    't341': ('T341', 'Hanshin Tigers (Japan)'),
    't430': ('T430', 'Mississippi Braves'),
    't445': ('T445', 'Columbus Clippers'),
    't452': ('t452', 'Altoona Curve'),
    't477': ('T477', 'Greensboro Grasshoppers'),
    't494': ('T493', 'Charlotte Knights'),
    't564': ('T564', 'Jacksonville Suns'),
    't569': ('T569', 'Quintana Roo Tigres'),
    't580': ('T580', 'Winston-Salem Dash'),
    't588': ('T588', 'New Orleans Zephyrs'),
    't784': ('T784', 'WBC Canada'),
    't805': ('T805', 'WBC Dominican Republic'),
    't841': ('T841', 'WBC Italy'),
    't878': ('T878', 'WBC Netherlands'),
    't890': ('T890', 'WBC Panama'),
    't897': ('T897', 'WBC Puerto Rico'),
    't944': ('T944', 'WBC Venezuela'),
    't940': ('T940', 'WBC United States'),
    't918': ('T918', 'WBC South Africa'),
    't867': ('T867', 'WBC Mexico'),
    't760': ('T760', 'WBC Australia'),
    't790': ('T790', 'WBC China'),
    't843': ('T843', 'WBC Japan'),
    't791': ('T791', 'WBC Taipei'),
    't798': ('T798', 'WBC Cuba'),
    't1171': ('T1171', 'WBC Korea'),
    't1193': ('T1193', 'WBC Venezuela'),
    't2290': ('T2290', 'University of Michigan'),
    't2330': ('T3330', 'Georgetown University'),
    't2330': ('T3330', 'Georgetown University'),
    't2291': ('T2291', 'St. Louis University'),
    't2292': ('T2292', 'University of Southern Florida'),
    't2510': ('T2510', 'Team Canada'),
    't4744': ('ABK', 'Army Black Knights'),
    'uga' : ('UGA',  'University of Georgia'),
    'mcc' : ('MCC', 'Manatee Community College'),
    'fso' : ('FSO', 'Florida Southern College'),
    'fsu' : ('FSU', 'Florida State University'),
    'neu' : ('NEU',  'Northeastern University'),
    'bc' : ('BC',  'Boston College', ''),
    }

STREAM_SPEEDS = ( '300', '500', '1200', '1800', '2400' )

NEXDEF_SPEEDS = ( '128', '500', '800', '1200', '1800', '2400', '3000', '4500' )

DEFAULT_SPEED = '1200'

DEFAULT_V_PLAYER = 'mplayer -cache 2048 -really-quiet'
DEFAULT_A_PLAYER = 'mplayer -cache 64 -really-quiet'

DEFAULT_FLASH_BROWSER='firefox %s'

BOOKMARK_FILE = os.path.join(os.environ['HOME'], AUTHDIR, 'bookmarks.pf')

KEYBINDINGS = { 'Up/Down'    : 'Highlight games in the current view',
                'Enter'      : 'Play video of highlighted game',
                'Left/Right' : 'Navigate one day forward or back',
                'c'          : 'Play Condensed Game Video (if available)',
                'j'          : 'Jump to a date',
                'm'          : 'Bookmark a game or edit bookmark title',
                'n'          : 'Toggle NEXDEF mode',
                'l (or Esc)' : 'Return to listings',
                'b'          : 'View line score',
                'z'          : 'Show listings debug',
                'o'          : 'Show options debug',
                'x (or Bksp)': 'Delete a bookmark',
                'r'          : 'Refresh listings',
                'q'          : 'Quit mlbviewer',
                'h'          : 'Display version and keybindings',
                'a'          : 'Play Gameday audio of highlighted game',
                'd'          : 'Toggle debug (does not change config file)',
                'p'          : 'Toggle speed (does not change config file)',
                's'          : 'Toggle coverage for HOME or AWAY stream',
                't'          : 'Display top plays listing for current game',
                'y'          : 'Play all highlights as a playlist',
              }

HELPFILE = (
    ('COMMANDS' , ( 'Enter', 'a', 'c', 'd', 'n', 's' )),
    ('LISTINGS', ( 'Up/Down', 'Left/Right', 'j', 'p', 'r' )),
    ('SCREENS'  , ( 't', 'h', 'l (or Esc)', 'b' )),
    ('DEBUG'    , ( 'z', 'o' )),
    )

KEYBINDINGS_1 = { 
    'UP'                  : 'Move cursor up in the current view',
    'DOWN'                : 'Move cursor down in current view',
    'VIDEO'               : 'Play video of highlighted game',
    'LEFT'                : 'Navigate one day back',
    'RIGHT'               : 'Navigate one day forward',
    'CONDENSED_GAME'      : 'Play Condensed Game Video (if available)',
    'JUMP'                : 'Jump to a date',
    'NEXDEF'              : 'Toggle NEXDEF mode',
    'LISTINGS'            : 'Return to listings',
    'INNINGS'             : 'Jump to specific half inning',
    'LINE_SCORE'          : 'View line score',
    'BOX_SCORE'           : 'View box score',
    'MASTER_SCOREBOARD'   : 'Master scoreboard view',
    'MEDIA_DEBUG'         : 'Show media listings debug',
    'OPTIONS'             : 'Show options debug',
    'REFRESH'             : 'Refresh listings',
    'QUIT'                : 'Quit mlbviewer',
    'HELP'                : 'Display version and keybindings',
    'AUDIO'               : 'Play Gameday audio of highlighted game',
    'ALT_AUDIO'           : 'Play Gameday alternate audio of highlighted game',
    'DEBUG'               : 'Toggle debug (does not change config file)',
    'SPEED'               : 'Toggle speed (does not change config file)',
    'COVERAGE'            : 'Toggle coverage for HOME or AWAY stream',
    'HIGHLIGHTS'          : 'Display top plays listing for current game',
    'HIGHLIGHTS_PLAYLIST' : 'Play all highlights as a playlist',
    'RSS'                 : 'RSS feed for MLB (or select team feed)',
    'MILBTV'              : 'Switch to MiLB.TV listings',
    'STANDINGS'           : 'View standings',
    'STATS'               : 'View hitting or pitching statistics',
    'CALENDAR'            : 'Calendar view',
    'MEDIA_DETAIL'        : 'Media detail view',
    }

STATKEYBINDINGS = {
     'PITCHING'           : 'View pitching leaders',
     'HITTING'            : 'View hitting leaders',
     'PLAYER'             : 'View career stats for highlighted player',
     'SEASON_TYPE'        : 'Toggles between all-time and current season leaders',
     'ACTIVE'             : 'Toggles between all-time and active leaders',
     'LEAGUE'             : 'Toggle between MLB, AL, and NL leaders',
     'SORT_ORDER'         : 'Toggle between default, ascending, and descending sort order',
     'SORT'               : 'Change the sort column',
     'TEAM'               : 'Filter leaders by team',
     'YEAR'               : 'Filter leaders by year',
     'UP'                 : 'Move the cursor up a line',
     'DOWN'               : 'Move the cursor down a line',
     'STATS_DEBUG'        : 'View raw data for highlighted line',
}

HELPBINDINGS = (
    ('COMMANDS', ('VIDEO', 'AUDIO', 'ALT_AUDIO', 'CONDENSED_GAME', 'DEBUG', 
                  'NEXDEF', 'COVERAGE', 'HIGHLIGHTS_PLAYLIST', 'INNINGS') ),
    ('LISTINGS', ('UP', 'DOWN', 'LEFT', 'RIGHT', 'JUMP', 'SPEED', 'REFRESH' )),
    ('SCREENS', ('HIGHLIGHTS', 'HELP', 'LISTINGS', 'LINE_SCORE', 'BOX_SCORE',
     'MASTER_SCOREBOARD', 'CALENDAR', 'STANDINGS', 'STATS', 'RSS', 'MILBTV',
     'MEDIA_DETAIL' ) ),
    ('DEBUG', ( 'OPTIONS', 'DEBUG', 'MEDIA_DEBUG' )),
    )

STATHELPBINDINGS = (
    ('SCREENS' , ('PITCHING', 'HITTING', 'PLAYER' ) ),
    ('FILTERS' , ('SEASON_TYPE', 'LEAGUE', 'SORT_ORDER', 'SORT', 'ACTIVE', 'TEAM', 'YEAR' ) ),
    ('LISTINGS', ('UP', 'DOWN' ) ),
    ('DEBUG'   , ( 'STATS_DEBUG', ) ),
    )

OPTIONS_DEBUG = ( 'video_player', 'audio_player', 'top_plays_player',
                  'speed', 'use_nexdef', 'use_wired_web', 'min_bps', 'max_bps',
                  'adaptive_stream', 'use_librtmp', 'live_from_start',
                  'video_follow', 'audio_follow', 'blackout', 'coverage',
                  'show_player_command', 'user' )

COLORS = { 'black'   : curses.COLOR_BLACK,
           'red'     : curses.COLOR_RED,
           'green'   : curses.COLOR_GREEN,
           'yellow'  : curses.COLOR_YELLOW,
           'blue'    : curses.COLOR_BLUE,
           'magenta' : curses.COLOR_MAGENTA,
           'cyan'    : curses.COLOR_CYAN,
           'white'   : curses.COLOR_WHITE,
           'xterm'   : -1
         }

# used for color pairs
COLOR_FAVORITE = 1
COLOR_FREE = 2

STATUSLINE = {
        "E" : "Status: Completed Early",
        "C" : "Status: Cancelled",
        "I" : "Status: In Progress",
        "W" : "Status: Not Yet Available",
        "F" : "Status: Final",
        "CG": "Status: Final (Condensed Game Available)",
        "P" : "Status: Not Yet Available",
        "S" : "Status: Suspended",
        "D" : "Status: Delayed",
        "IP": "Status: Pregame",
        "PO": "Status: Postponed",
        "GO": "Status: Game Over - stream not yet available",
        "NB": "Status: National Blackout",
        "LB": "Status: Local Blackout"}

SPEEDTOGGLE = {
        "300"  : "[ 300K]",
        "500"  : "[ 500K]",
        "1200" : "[1200K]",
        "1800" : "[1800K]",
        "2400" : "[2400K]"}

COVERAGETOGGLE = {
    "away" : "[AWAY]",
    "home" : "[HOME]"}

SSTOGGLE = {
    True  : "[>>]",
    False : "[--]"}


UNSUPPORTED = 'ERROR: That key is not supported in this screen'

# for line scores
RUNNERS_ONBASE_STATUS = {
    '0': 'Empty',
    '1': '1B',
    '2': '2B',
    '3': '3B',
    '4': '1B and 2B',
    '5': '1B and 3B',
    '6': '2B and 3B',
    '7': 'Bases loaded',
}

RUNNERS_ONBASE_STRINGS = {
    'runner_on_1b': 'Runner on 1B',
    'runner_on_2b': 'Runner on 2B',
    'runner_on_3b': 'Runner on 3B',
}

STANDINGS_DIVISIONS = {
    'MLB.AL.E':  'AL East',
    'MLB.AL.C':  'AL Central',
    'MLB.AL.W':  'AL West',
    'MLB.NL.E':  'NL East',
    'MLB.NL.C':  'NL Central',
    'MLB.NL.W':  'NL West',
}

STANDINGS_JSON_DIVISIONS = {
    '201' : 'AL East',
    '202' : 'AL Central',
    '200' : 'AL West',
    '204' : 'NL East',
    '205' : 'NL Central',
    '203' : 'NL West',
}


# To Add New Sections for MLB.COM Video viewer:
# 1. Use Firefox Web Console on the Results page to be added.
# 2. Look for the request with a URL like:
#    GET http://wapc.mlb.com/ws/search/MediaSearchService?start=1&hitsPerPage=200&type=json&sort=desc&sort_type=date&mlbtax_key=sf_the_franchise
# 3. Use the &mlbtax_key= value, in this case, sf_the_franchise.
# 4. Pick a menu location and assign this new entry a numerical ID.  This
#    menu is sorted in numerical order.
# 5. For example, choose 1190 to place this after the 2012 Postseason.  There
#    is plenty of numerical space to squeeze in new entries or shift things 
#    around.  So this could also be 1005 to place it right after FastCast.
#    In the same way, if Game Recaps is desired at a higher position, change
#    1210 to a lower number such as 1005 to place it after FastCast or 990
#    to place it before FastCast, e.g. top of the menu.
# 6. Some requests include an mmtax_key in addition to an mlbtax_key.  See
#    1010 for an example of how to include that.
# 7. Some requests include an mmtax_key instead of an mlbtax_key such as:
#    GET http://wapc.mlb.com/ws/search/MediaSearchService?start=1&hitsPerPage=200&type=json&sort=desc&sort_type=date&mmtax_key=mlb_prod_player_poll
#    See 1130 for an example of how to include an mmtax_key without an 
#    mlbtax_key.  Or 1180 for an example without mmtax_key or mlbtax_key.
# 8. After entering the request key in MLBCOM_VIDKEYS, create a matching
#    entry in MLBCOM_VIDTITLES using the same numerical key with the 
#    desired menu entry title.  When changing a numerical key in VIDKEYS,
#    also change the corresponding numerical key in VIDTITLES too.
#
# The main video browser on mlb.com: http://wapc.mlb.com/play
# TODO: Add the "More To Explore" subsections.

MLBCOM_VIDKEYS = {
    '1800'    : 'vtp_pulse',
    '900'    : 'vtp_daily_dash',
    '910'    : 'top_5&mmtax_key=2013&op=and',
    '1000'   : 'fastcast%2Bvtp_fastcast',
#    '1005'   : 'mm_wrapup',
    '1008'   : 'all_star_game&mmtax_key=2014&op=and',
    '1010'   : 'vtp_head_and_shoulders&mmtax_key=2014&op=and',
#    '1020'   : 'vtp_blackberry',
#    '1030'   : 'stand_up_to_cancer',
    '1040'   : 'the_wall',
    '1050'   : 'vtp_must_c',
#    '1060'   : 'vtp_jiffy_lube&mmtax_key=2014&op=and',
#    '1200'   : 'meggie_zahneis',
    '1220'   : 'vtp_budweiser',
    '1225'   : 'edward_jones%2Bvtp_manager_postgame&op=or',
    '1230'   : 'vtp_chatting_cage',
    '1250'   : 'mlb_draft&mmtax_key=2014&op=and',
    '1300'   : 'this_week_in_baseball',
    '1310'   : 'mlb_network',
#    '1320'   : 'mlbn_diamond_demos',
#    '1330'   : 'prime9%2Bmlb_productions&op=and',
    '1500'   : 'walk_off_rbi&op=or',
    '1510'   : 'error',
    '1520'   : 'home_run',
    '1530'   : 'blooper',
    '1540'   : 'defense',
    '1550'   : 'no_hitter%2Bperfect_game&op=or',
    '1600'   : 'vtp_fan_clips',
    '1610'   : 'vtp_bucks',
#    '1700'   : 'mlb_productions',
#    '1710'   : 'mlb_productions_world_series',
#    '1720'   : 'sho_franchise&mmtax_key=2012&op=and',
#    '1730'   : 'sf_the_franchise',
#    '1740'   : '&mmtax_key=mlb_prod_player_poll',
    '1900'   : 'world_series&mmtax_key=2013&op=and',
    '1910'   : 'alcs&mmtax_key=2013&op=and',
    '1920'   : 'nlcs&mmtax_key=2013&op=and',
    '1930'   : '&mmtax_key=2013%2Balds_b&op=and',
    '1940'   : '&mmtax_key=2013%2Balds_a&op=and',
    '1950'   : '&mmtax_key=2013%2Bnlds_a&op=and',
    '1960'   : '&mmtax_key=2013%2Bnlds_b&op=and',
    '1970'   : '&game=345594',
    '1980'   : '&game=345595',
    '9000'   : 'bb_moments',
}

MLBCOM_VIDTITLES = {
    '1800'    : 'Pulse Of The Postseason',
    '900'    : 'Daily Dash',
    '910'    : 'Top 5 Plays Of The Day',
    '1000'   : 'MLB.com FastCast',
#    '1005'   : 'Daily Recaps',
    '1008'   : '2014 MLB All-Star Game',
    '1010'   : 'Top Pitching Performances',
#    '1020'   : 'The MLB.com Flow',
#    '1030'   : 'Stand Up To Cancer',
    '1040'   : 'Cut4',
    '1050'   : 'Must C',
#    '1060'   : 'Highly Trained Performances',
#    '1200'   : 'Youth Reporter: Meggie Zahneis',
    '1220'   : '2014 MLB Walk-Offs',
    '1225'   : 'Edward Jones Face Time',
    '1230'   : 'Edward Jones Chatting Cage',
    '1250'   : '2014 MLB Draft',
    '1300'   : 'MLB Network: This Week In Baseball',
    '1310'   : 'MLB Network: MLB Network',
#    '1320'   : 'MLB Network: Diamond Demos',
#    '1330'   : 'MLB Network: Prime 9',
    '1500'   : 'Game Highlights: Walk-Offs',
    '1510'   : 'Game Highlights: Errors',
    '1520'   : 'Game Highlights: Home Runs',
    '1530'   : 'Game Highlights: Baseball Oddities',
    '1540'   : 'Game Highlights: Top Defensive Plays',
    '1550'   : 'Game Highlights: No-Hitters & Perfect Games',
    '1600'   : 'Fan Favorite Moments',
    '1610'   : 'Bucks on the Pond',
#    '1700'   : 'MLB Productions: MLB Productions',
#    '1710'   : 'MLB Productions: World Series',
#    '1720'   : 'MLB Productions: The Franchise: Miami Marlins',
#    '1730'   : 'MLB Productions: The Franchise',
#    '1740'   : 'MLB Productions: MLB Player Poll',
    '1900'   : '2013 Postseason: 2013 World Series',
    '1910'   : '2013 Postseason: ALCS',
    '1920'   : '2013 Postseason: NLCS',
    '1930'   : '2013 Postseason: ALDS: Athletics vs. Tigers',
    '1940'   : '2013 Postseason: ALDS: Red Sox vs. Rays',
    '1950'   : '2013 Postseason: NLDS: Pirates vs. Cardinals',
    '1960'   : '2013 Postseason: NLDS: Braves vs. Dodgers',
    '1970'   : '2013 Postseason: AL Wildcard',
    '1980'   : '2013 Postseason: NL Wildcard',
    '9000'   : "Baseball's Best Moments",
}

STATFILE = 'statconfig'

STATS_LEAGUES = ( 'MLB', 'NL', 'AL' )

STATS_SEASON_TYPES = ( 'ANY', 'ALL' )

STATS_SORT_ORDER = ( 'default', 'asc', 'desc' )

STATS_TEAMS = {
      0 : 'mlb',
    108 : 'ana',
    109 : 'ari',
    110 : 'bal',
    111 : 'bos',
    112 : 'chc',
    113 : 'cin',
    114 : 'cle',
    115 : 'col',
    116 : 'det',
    117 : 'hou',
    118 : 'kc',
    119 : 'la',
    120 : 'was',
    121 : 'nym',
    133 : 'oak',
    134 : 'pit',
    135 : 'sd',
    136 : 'sea',
    137 : 'sf',
    138 : 'stl',
    139 : 'tb',
    140 : 'tex',
    141 : 'tor',
    142 : 'min',
    143 : 'phi',
    144 : 'atl',
    145 : 'cws',
    146 : 'mia',
    147 : 'nyy',
    158 : 'mil',
}

DAYS_OF_WEEK = {
    0 : 'MON',
    1 : 'TUE',
    2 : 'WED',
    3 : 'THU',
    4 : 'FRI',
    5 : 'SAT',
    6 : 'SUN',
}

CLASSICS_ENTRY_SORT = ( 'title', 'published' )
