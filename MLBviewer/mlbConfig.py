#!/usr/bin/env python

import os
import re
import sys
import tty
import termios
from mlbConstants import MLBLIVE

class MLBConfig:

    def __init__(self, default_dct=dict()):
        self.data = default_dct

    def exit(self):
        # MLBLIVE is a Live DVD/VM version of mlbviewer.  The application
        # is started with an icon click.  The first messages from new()
        # happen before curses is initialized so another way is needed to
        # delay application exit long enough for user to read the messages.
        # Thank you, StackOverflow, for the recipe using tty and termios.

        if not MLBLIVE:
            sys.exit()

        # Inside mlblive.  Grab an acknowledgement before closing window.
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            print
            print "Press any key to exit..."
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            sys.exit()

    def new(self, config, defaults, dir):
        #conf = os.path.join(os.environ['HOME'], authfile)
        print "Creating configuration files"
        if dir:
            try:
                os.mkdir(dir)
            except:
                print 'Could not create directory: ' + dir + '\n'
                print 'See README for configuration instructions\n'
                self.exit()
        # now write the config file
        try:
            fp = open(config,'w')
        except:
            print 'Could not write config file: ' + config
            print 'Please check directory permissions.'
            self.exit()
        fp.write('# See README for explanation of these settings.\n')
        fp.write('# user and pass are required except for Top Plays\n\n')
        fp.write('user=\n\n')
        fp.write('pass=\n\n')
        for k in ( 'video_player' , 'audio_player', 'favorite', 'use_nexdef', 'speed', 'min_bps', 'max_bps', 'adaptive_stream' ):
            if type(defaults[k]) == type(list()):
                if len(defaults[k]) > 0:
                    for item in defaults[k]:
                        fp.write(k + '=' + str(item) + '\n')
                    fp.write('\n')
                else:
                    fp.write(k + '=' + '\n\n')
            else:
                fp.write(k + '=' + str(defaults[k]) + '\n\n')
        fp.write('# Many more options are available and documented at:\n')
        fp.write('# http://sourceforge.net/p/mlbviewer/wiki/Home/\n')
        fp.close()
        print
        print 'Configuration complete!  You are now ready to use mlbviewer.'
        print
        print 'Configuration file written to: '
        print
        print config
        print
        print 'Please review the settings.  You will need to set user and pass.'
        self.exit()



    def loads(self, authfile):
        #conf = os.path.join(os.environ['HOME'], authfile)
        fp = open(authfile)

        for line in fp:
            # Skip all the comments
            if line.startswith('#'):
                pass
            # Skip all the blank lines
            elif re.match(r'^\s*$',line):
                pass
            else:
            # Break at the first equals sign
                key, val = line.split('=')[0], '='.join(line.split('=')[1:])
                key = key.strip()
                val = val.strip()
                # These are the ones that take multiple values
                if key in ('blackout', 'audio_follow', 'alt_audio_follow', 'video_follow', 'favorite', 'classics_users'):
                    if val not in self.data[key] and val != '':
                        self.data[key].append(val)
                # These are the booleans:
                elif key in ('show_player_command', 'debug', 'use_color', 
                             'live_from_start', 'use_nexdef', 'milbtv',
                             'adaptive_stream', 'show_inning_frames', 
                             'postseason', 'use_librtmp', 'no_lirc', 
                             'disable_favorite_follow',
                             'highlight_division',
                             'gameday_audio',
                             'curses_debug', 'use_wired_web' ):
                    if val.isdigit():
                        self.data[key] = bool(int(val))
                    else:
                        if val.lower() in ('false', 'no', 'none'):
                            self.data[key] = False
                        elif val.lower() in ('true', 'yes'):
                            self.data[key] = True
                        # Otherwise stick with the default.
                        else:
                            pass
                # And these are the ones that only take one value, and so,
                # replace the defaults.
                else:
                    self.data[key] = val

    def get(self,key):
        try:
            return self.data[key]
        except:
            return None

    def set(self,key,value):
        if key in ( 'video_follow', 'audio_follow', 'alt_audio_follow' ):
            self.data[key].append(value)
        else:
            try:
                self.data[key] = value
            except:
                return None
