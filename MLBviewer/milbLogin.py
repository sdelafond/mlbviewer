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

import urllib
import urllib2
import re
import time
import datetime
import cookielib

import os
import sys

from mlbLog import MLBLog

# DEBUG VARIABLES
# Cookie debug writes cookie contents to cookielog
COOKIE_DEBUG=True

# If this is set to True, all cookie morsels are written to cookie file
# else if morsels are marked as discard, then they are not written to file
IGNORE_DISCARD=True

# DO NOT EDIT BELOW HERE

AUTHDIR = '.mlb'
COOKIEFILE = os.path.join(os.environ['HOME'], AUTHDIR, 'milbcookie')
SESSIONKEY = os.path.join(os.environ['HOME'], AUTHDIR, 'milbsessionkey')
LOGFILE = os.path.join(os.environ['HOME'], AUTHDIR, 'cookielog')
USERAGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13'

class Error(Exception):
    pass

class MLBNoCookieFileError(Error):
    pass

class MLBAuthError(Error):
    pass

class MiLBSession:

    def __init__(self,user,passwd,debug=False):
        self.user = user
        if self.user is None:
            # if user= is commented out, cfg.get() returns None, normalize this
            self.user = ""
        self.passwd = passwd
        self.auth = True
        self.logged_in = None
        self.cookie_jar = None
        self.cookies = {}
        self.debug = debug
        if COOKIE_DEBUG:
            self.debug = True
        self.log = MLBLog(LOGFILE)
        try:
            self.session_key = self.readSessionKey()
            if self.debug:
                self.log.write("LOGIN> Read session key from file: " + str(self.session_key))
        except:
            self.session_key = None

    def readSessionKey(self):
        sk = open(SESSIONKEY,"r")
        self.session_key = sk.read()
        sk.close()
        return session_key

    def writeSessionKey(self,session_key):
        if self.debug:
            self.log.write('Writing session-key to file: ' + str(self.session_key) + '\n')
        sk = open(SESSIONKEY,"w")
        sk.write(session_key)
        sk.close()
        return session_key

    def extractCookies(self):
        for c in self.cookie_jar:
            self.cookies[c.name] = c.value
        self.printCookies()

    def printCookies(self):
        if self.debug:
            self.log.write('Printing relevant cookie morsels...\n')
            for name in self.cookies.keys():
                if name in ('fprt', 'ftmu', 'ipid'):
                    self.log.write(str(name) + ' = ' + str(self.cookies[name]))
                    self.log.write('\n')

    def readCookieFile(self):
        self.cookie_jar = cookielib.LWPCookieJar()
        if self.cookie_jar != None:
            if os.path.isfile(COOKIEFILE):
                self.cookie_jar.load(COOKIEFILE,ignore_discard=IGNORE_DISCARD)
                if self.debug:
                    self.log.write('readCookieFile:\n')
                self.extractCookies()
            else:
                raise MLBNoCookieFileError
        else:
            self.error_str = "Couldn't open cookie jar"
            raise Exception,self.error_str

    def login(self):
        try:
            self.readCookieFile()
        except MLBNoCookieFileError:
            #pass
            if self.debug:
                self.log.write("LOGIN> No cookie file")
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie_jar))
        urllib2.install_opener(opener)

        # First visit the login page and get the session cookie
        login_url = 'https://secure.milb.com/enterworkflow.do?flowId=registration.profile'
        txheaders = {'User-agent' : USERAGENT}
        data = None
        req = urllib2.Request(login_url,data,txheaders)
        # we might have cookie info by now??
        if self.user=="":
            return

        try:
            handle = urllib2.urlopen(req)
        except:
            self.error_str = 'Error occurred in HTTP request to login page'
            raise Exception, self.error_str
        try:
            if self.debug:
                self.log.write('pre-login:\n')
            self.extractCookies()
        except Exception,detail:
            raise Exception,detail
        #if self.debug:
        #    self.log.write('Did we receive a cookie from the wizard?\n')
        #    for index, cookie in enumerate(self.cookie_jar):
        #        print >> self.log, index, ' : ' , cookie
        self.cookie_jar.save(COOKIEFILE,ignore_discard=IGNORE_DISCARD)

        rdata = handle.read()

        # now authenticate
        auth_values = {'uri' : '/account/login_register.jsp',
                       'registrationAction' : 'identify',
                       'emailAddress' : self.user,
                       'password' : self.passwd
                      }
        success_pat = re.compile(r'Account Management - Profile | MiLB.com Account |')
        auth_data = urllib.urlencode(auth_values)
        auth_url = 'https://secure.milb.com/authenticate.do'
        req = urllib2.Request(auth_url,auth_data,txheaders)
        try:
            handle = urllib2.urlopen(req)
            self.cookie_jar.save(COOKIEFILE,ignore_discard=IGNORE_DISCARD)
            if self.debug:
                self.log.write('post-login: (this gets saved to file)\n')
            self.extractCookies()
        except:
            self.error_str = 'Error occurred in HTTP request to auth page'
            raise Exception, self.error_str
        auth_page = handle.read()
        #if self.debug:
        #    self.log.write('Did we receive a cookie from authenticate?\n')
        #    for index, cookie in enumerate(self.cookie_jar):
        #        print >> self.log, index, ' : ' , cookie
        self.cookie_jar.save(COOKIEFILE,ignore_discard=IGNORE_DISCARD)
        try:
           loggedin = re.search(success_pat, auth_page).groups()
           self.log.write('Logged in successfully!\n')
           self.logged_in = True
        except:
           self.error_str = 'Login was unsuccessful.'
           self.log.write(auth_page)
           os.remove(COOKIEFILE)
           raise MLBAuthError, self.error_str
        #if self.debug:
        #   self.log.write("DEBUG>>> writing login page")
        #   self.log.write(auth_page)
        # END login()
  
    def getSessionData(self):
        # This is the workhorse routine.
        # 1. Login
        # 2. Get the url from the workflow page
        # 3. Logout
        # 4. Return the raw workflow response page
        # The hope is that this sequence will always be the same and leave
        # it to url() to determine if an error occurs.  This way, hopefully,
        # error or no, we'll always log out.
        if self.cookie_jar is None:
            if self.logged_in is None:
                login_count = 0
                while not self.logged_in:
                    if self.user=="":
                        break
                    try:
                        self.login()
                    except:
                        if login_count < 3:
                            login_count += 1
                            time.sleep(1)
                        else:
                            raise
                            #raise Exception,self.error_str
                # clear any login unsuccessful messages from previous failures
                if login_count > 0:
                    self.error_str = "Not logged in."

        wf_url = 'http://www.milb.com/index.jsp?flowId=media.media'

        # Open the workflow url...
        # Get the session key morsel
        referer_str = ''
        txheaders = {'User-agent' : USERAGENT,
                     'Referer'    : referer_str }
        req = urllib2.Request(url=wf_url,headers=txheaders,data=None)
        try:
            handle = urllib2.urlopen(req)
            if self.debug:
                self.log.write('getSessionData:\n')
            self.extractCookies()
        except Exception,detail:
            self.error_str = 'Not logged in'
            raise Exception, self.error_str
        url_data = handle.read()
        #if self.debug:
        #    if self.auth:
        #        self.log.write('Did we receive a cookie from workflow?\n')
        #        for index, cookie in enumerate(self.cookie_jar):
        #            print >> self.log, index, ' : ' , cookie
        if self.auth:
            self.cookie_jar.save(COOKIEFILE,ignore_discard=IGNORE_DISCARD)
        #if self.debug:
        #   self.log.write("DEBUG>>> writing workflow page")
        #   self.log.write(url_data)
        return url_data

    def logout(self):
        """Logs out from the mlb.com session. Meant to prevent
        multiple login errors."""
        LOGOUT_URL="https://secure.mlb.com/enterworkflow.do?flowId=registration.logout&c_id=mlb"
        txheaders = {'User-agent' : USERAGENT,
                     'Referer' : 'http://mlb.mlb.com/index.jsp'}
        data = None
        req = urllib2.Request(LOGOUT_URL,data,txheaders)
        handle = urllib2.urlopen(req)
        logout_info = handle.read()
        handle.close()
        pattern = re.compile(r'You are now logged out.')
        if not re.search(pattern,logout_info):
           self.error_str = "Logout was unsuccessful. Check " + LOGFILE
           self.log.write(logout_info)
           raise MLBAuthError, self.error_str
        else:
           self.log.write('Logged out successfully!\n')
           self.logged_in = None
        if self.debug:
           self.log.write("DEBUG>>> writing logout page")
           self.log.write(logout_info)
        # clear session cookies since they're no longer valid
        self.log.write('Clearing session cookies\n')
        self.cookie_jar.clear_cookie_jar()
        # session is bogus now - force a new login each time
        self.cookie_jar = None
        # END logout

