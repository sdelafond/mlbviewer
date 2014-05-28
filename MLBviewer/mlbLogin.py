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
COOKIEFILE = os.path.join(os.environ['HOME'], AUTHDIR, 'cookie')
SESSIONKEY = os.path.join(os.environ['HOME'], AUTHDIR, 'sessionkey')
LOGFILE = os.path.join(os.environ['HOME'], AUTHDIR, 'cookielog')
USERAGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13'

class Error(Exception):
    pass

class MLBNoCookieFileError(Error):
    pass

class MLBAuthError(Error):
    pass

class MLBSession:

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
        self.log.write('MLBSession BEGIN')
        try:
            self.session_key = self.readSessionKey()
            self.log.write('init() session-key : ' + self.session_key)
        except:
            #raise
            self.log.write('init() session-key : None')
            self.session_key = None

    def readSessionKey(self):
        sk = open(SESSIONKEY,"r")
        self.session_key = sk.read()
        sk.close()
        return self.session_key

    def writeSessionKey(self,session_key):
        self.session_key = session_key
        self.log.write('writeSessionKey(): ' + str(self.session_key))
        sk = open(SESSIONKEY,"w")
        sk.write(self.session_key)
        sk.close()
        return self.session_key

    def extractCookies(self):
        for c in self.cookie_jar:
            self.cookies[c.name] = c.value
        self.printCookies()

    def printCookies(self):
        self.log.write('printCookies() : ')
        for name in self.cookies.keys():
            if name in ('fprt', 'ftmu', 'ipid'):
                self.log.write(str(name) + ' = ' + str(self.cookies[name]))

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
        callback = str(int(time.time() * 1000))
        login_url = 'http://mlb.mlb.com/account/quick_login_hdr.jsp?'\
            'successRedirect=http://mlb.mlb.com/shared/account/v2/login_success.jsp'\
            '%3Fcallback%3Dl' + callback + '&callback=l' + callback + \
            '&stylesheet=/style/account_management/myAccountMini.css&submitImage='\
            '/shared/components/gameday/v4/images/btn-login.gif&'\
            'errorRedirect=http://mlb.mlb.com/account/quick_login_hdr.jsp%3Ferror'\
            '%3Dtrue%26successRedirect%3Dhttp%253A%252F%252Fmlb.mlb.com%252Fshared'\
            '%252Faccount%252Fv2%252Flogin_success.jsp%25253Fcallback%25253Dl' +\
            callback + '%26callback%3Dl' + callback + '%26stylesheet%3D%252Fstyle'\
            '%252Faccount_management%252FmyAccountMini.css%26submitImage%3D%252F'\
            'shared%252Fcomponents%252Fgameday%252Fv4%252Fimages%252Fbtn-login.gif'\
            '%26errorRedirect%3Dhttp%3A//mlb.mlb.com/account/quick_login_hdr.jsp'\
            '%253Ferror%253Dtrue%2526successRedirect%253Dhttp%25253A%25252F%25252F'\
            'mlb.mlb.com%25252Fshared%25252Faccount%25252Fv2%25252Flogin_success.jsp'\
            '%2525253Fcallback%2525253Dl' + callback + '%2526callback%253Dl' +\
            callback + '%2526stylesheet%253D%25252Fstyle%25252Faccount_management'\
            '%25252FmyAccountMini.css%2526submitImage%253D%25252Fshared%25252F'\
            'components%25252Fgameday%25252Fv4%25252Fimages%25252Fbtn-login.gif'
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
                self.log.write('pre-login:')
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
        auth_values = {'emailAddress' : self.user,
                       'password' : self.passwd,
                       'submit.x' : 25,
                       'submit.y' : 7}
        g = re.search('name="successRedirect" value="(?P<successRedirect>[^"]+)"', rdata)
        auth_values['successRedirect'] = g.group('successRedirect')
        g = re.search('name="errorRedirect" value="(?P<errorRedirect>[^"]+)"', rdata)
        auth_values['errorRedirect'] = g.group('errorRedirect')
        auth_data = urllib.urlencode(auth_values)
        auth_url = 'https://secure.mlb.com/account/topNavLogin.jsp'
        req = urllib2.Request(auth_url,auth_data,txheaders)
        try:
            handle = urllib2.urlopen(req)
            self.cookie_jar.save(COOKIEFILE,ignore_discard=IGNORE_DISCARD)
            if self.debug:
                self.log.write('post-login: (this gets saved to file)')
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
           loggedin = re.search('Login Success', auth_page).groups()
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

        wf_url = "http://www.mlb.com/enterworkflow.do?" +\
            "flowId=media.media"

        # Open the workflow url...
        # Get the session key morsel
        referer_str = ''
        txheaders = {'User-agent' : USERAGENT,
                     'Referer'    : referer_str }
        req = urllib2.Request(url=wf_url,headers=txheaders,data=None)
        try:
            handle = urllib2.urlopen(req)
            if self.debug:
                self.log.write('extractCookies():')
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

