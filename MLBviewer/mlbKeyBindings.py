#!/usr/bin/env python

import os
import re

from mlbDefaultKeyBindings import DEFAULT_KEYBINDINGS

class MLBKeyBindings:

    def __init__(self, default_dct=dict()):
        self.data = default_dct

    def loads(self, keyfile):
        #conf = os.path.join(os.environ['HOME'], keyfile)
        try:
            fp = open(keyfile)
        except:
            return

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
                # Certain keys will retain their default bindings but can
                # include additional bindings
                if key in ( 'UP', 'DOWN', 'LEFT', 'RIGHT', 'HELP',
                    'VIDEO', 'AUDIO' ):
                    if val != "" and val not in self.data[key]:
                        if val.isdigit():
                            self.data[key].append(int(val))
                        else:
                            self.data[key].append(ord(val))
                elif val.isdigit():
                    self.data[key] = [ int(val) ]
                # And these are the ones that only take one value, and so,
                # replace the defaults.
                else:
                    try:
                        self.data[key] = [ ord(val) ]
                    except:
                        raise Exception,"Invalid keybinding: %s = %s" %\
                            ( key, val )

    def get(self,key):
        try:
            return self.data[key]
        except:
            raise
            return None

    def set(self,key,value):
        try:
            if isinstance(value, int) or value.isdigit():
                self.data[key] = [ value ]
            else:
                self.data[key] = [ ord(value) ]
        except:
            #raise
            return None

    def macro(self,value):
        TRANSLATE = {
            10  : 'Enter',
            27  : 'Esc' ,
            258 : 'Down',
            259 : 'Up',
            260 : 'Left',
            261 : 'Right',
            409 : 'Mouse (if enabled)',
        }
        if TRANSLATE.has_key(value):
            return TRANSLATE[value]
        elif value > 32 and value < 127:
            # if it is a printable ascii character, print the char value
            return str(unichr(value))
        else:
            return value

