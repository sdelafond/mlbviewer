#!/usr/bin/env python
 
# $Revision$

import os.path
import sys
import re
import subprocess

import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)

#from suds.client import Client
#from suds import WebFault

import xml.etree.ElementTree
from xml.dom.minidom import parse
from xml.dom.minidom import parseString

def printChildNodes(node,IL):
  if node.hasChildNodes():
    print "%s %s:" % (IL*' ', node.nodeName)
    IL += 1
    for child in node.childNodes:
      printChildNodes(child,IL)
  else:
    print "%s %s: %s" % (IL*' ', node.nodeName, node.nodeValue)
    IL -= 1


url = 'file://'
url += os.path.join(os.environ['HOME'], '.mlb', 'MediaService.wsdl')
#client = Client(url)

SESSIONKEY = os.path.join(os.environ['HOME'], '.mlb', 'sessionkey')

SOAPCODES = {
    "1"    : "OK",
    "-1000": "Requested Media Not Found",
    "-1500": "Other Undocumented Error",
    "-2000": "Authentication Error",
    "-2500": "Blackout Error",
    "-3000": "Identity Error",
    "-3500": "Sign-on Restriction Error",
    "-4000": "System Error",
}


bSubscribe = False

cj = None
cookielib = None

try: 
    EVENT = sys.argv[1]
except:
    #EVENT = '164-251363-2009-03-17'
    #EVENT = '14-257635-2009-03-26'
    #EVENT = '14-257676-2009-03-29'
    EVENT = '164-251362-2009-03-16'

try:
    SCENARIO = sys.argv[3]
except:
    #SCENARIO = "MLB_FLASH_800K_STREAM"
    SCENARIO = "FMS_CLOUD"
    #SCENARIO = "FLASH_1200K_800X448"
    #SCENARIO = "FLASH_1800K_800X448"

try:
    content_id = sys.argv[2]
except:
    content_id = None

try:
    play_path = sys.argv[4]
except:
    play_path = None

try:
    app = sys.argv[5]
except:
    app = None

try:
    session = sys.argv[6]
except:
    session = None

if session is None:
    try:
        sk = open(SESSIONKEY,"r")
        session = sk.read()
    	sk.close()
    except:
        print "no sessionkey file found."

COOKIEFILE = 'mlbcookie.lwp'
try:
    os.remove(COOKIEFILE)
except:
    pass

AUTHFILE = os.path.join(os.environ['HOME'],'.mlb/config')
 
DEFAULT_PLAYER = 'xterm -e mplayer -cache 2048 -quiet -fs'
DEFAULT_RECORDER = 'rtmpdump -f \"LNX 10,0,22,87\" -r %s'

try:
   import cookielib
except ImportError:
   raise Exception,"Could not load cookielib"

import urllib2
import urllib

conf = os.path.join(os.environ['HOME'], AUTHFILE)
fp = open(conf)

datadct = {'video_player': DEFAULT_PLAYER,
           'video_recorder': DEFAULT_RECORDER,
           'blackout': []}

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
        if key in ('blackout'):
            datadct[key].append(val)
        # And these are the ones that only take one value, and so,
        # replace the defaults.
        else:
            datadct[key] = val


cj = cookielib.LWPCookieJar()

if cj != None:
   if os.path.isfile(COOKIEFILE):
      cj.load(COOKIEFILE)
   if cookielib:
      opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
      urllib2.install_opener(opener)

# Get the cookie first
theurl = 'https://secure.mlb.com/enterworkflow.do?flowId=registration.wizard&c_id=mlb'
txheaders = {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13'}
data = None
req = urllib2.Request(theurl,data,txheaders)
response = urllib2.urlopen(req)
print 'These are the cookies we have received so far :'
for index, cookie in enumerate(cj):
    print index, '  :  ', cookie        
cj.save(COOKIEFILE,ignore_discard=True) 

# now authenticate
theurl = 'https://secure.mlb.com/authenticate.do'
txheaders = {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13',
             'Referer' : 'https://secure.mlb.com/enterworkflow.do?flowId=registration.wizard&c_id=mlb'}
values = {'uri' : '/account/login_register.jsp',
          'registrationAction' : 'identify',
          'emailAddress' : datadct['user'],
          'password' : datadct['pass']}

data = urllib.urlencode(values)
try:
   req = urllib2.Request(theurl,data,txheaders)
   response = urllib2.urlopen(req)
except IOError, e:
   print 'We failed to open "%s".' % theurl
   if hasattr(e, 'code'):
       print 'We failed with error code - %s.' % e.code
   elif hasattr(e, 'reason'):
       print "The error object has the following 'reason' attribute :", e.reason
       print "This usually means the server doesn't exist, is down, or we don't have an internet connection."
       sys.exit()

else:
    print 'Here are the headers of the page :'
    print response.info()                             # handle.read() returns the page, handle.geturl() returns the true url of the page fetched (in case urlopen has followed any redirects, which it sometimes does)

print
if cj == None:
    print "We don't have a cookie library available - sorry."
    print "I can't show you any cookies."
else:
    print 'These are the cookies we have received so far :'
    for index, cookie in enumerate(cj):
        print index, '  :  ', cookie        
    cj.save(COOKIEFILE,ignore_discard=True) 

page = response.read()
pattern = re.compile(r'Welcome to your personal (MLB|mlb).com account.')
try:
    loggedin = re.search(pattern, page).groups()
    print "Logged in successfully!"
except:
    raise Exception,page

# Begin MORSEL extraction
ns_headers = response.headers.getheaders("Set-Cookie")
attrs_set = cookielib.parse_ns_headers(ns_headers)
cookie_tuples = cookielib.CookieJar()._normalized_cookie_tuples(attrs_set)
print repr(cookie_tuples)
cookies = {}
for tup in cookie_tuples:
    name, value, standard, rest = tup
    cookies[name] = value
print repr(cookies)
print "ipid = " + str(cookies['ipid']) + " fingerprint = " + str(cookies['fprt'])
#print "session-key = " + str(cookies['ftmu'])
#sys.exit()
# End MORSEL extraction


# pick up the session key morsel
theurl = 'http://mlb.mlb.com/enterworkflow.do?flowId=media.media'
txheaders = {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13'}
data = None
req = urllib2.Request(theurl,data,txheaders)
response = urllib2.urlopen(req)

# Begin MORSEL extraction
ns_headers = response.headers.getheaders("Set-Cookie")
attrs_set = cookielib.parse_ns_headers(ns_headers)
cookie_tuples = cookielib.CookieJar()._normalized_cookie_tuples(attrs_set)
print repr(cookie_tuples)
#cookies = {}
for tup in cookie_tuples:
    name, value, standard, rest = tup
    cookies[name] = value
#print repr(cookies)
print "ipid = " + str(cookies['ipid']) + " fingerprint = " + str(cookies['fprt'])
try:
    print "session-key = " + str(cookies['ftmu'])
    session = urllib.unquote(cookies['ftmu'])
    #sk = open(SESSIONKEY,"w")
    #sk.write(session)
    #sk.close()

except:
    logout_url = 'https://secure.mlb.com/enterworkflow.do?flowId=registration.logout&c_id=mlb'
    txheaders = {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13',
             'Referer' : 'http://mlb.mlb.com/index.jsp'}
    data = None
    req = urllib2.Request(logout_url,data,txheaders)
    response = urllib2.urlopen(req)
    logout_info = response.read()
    response.close()
    print "No session key, so logged out."
    #session = None

event_id = EVENT
#pd = {'event-id':event_id, 'subject':'LIVE_EVENT_COVERAGE' }
#reply = client.service.find(**pd)
values = {
    'eventId': event_id, 
    'sessionKey': session,
    'fingerprint': urllib.unquote(cookies['fprt']),
    'identityPointId': cookies['ipid'],
    'subject':'LIVE_EVENT_COVERAGE'
}
theUrl = 'https://secure.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.1?' +\
    urllib.urlencode(values)
req = urllib2.Request(theUrl, None, txheaders);
response = urllib2.urlopen(req).read()
#print response
IL=0
xp = parseString(response)
printChildNodes(xp, IL)

el = xml.etree.ElementTree.XML(response)
utag = re.search('(\{.*\}).*', el.tag).group(1)
status = el.find(utag + 'status-code').text

try:
    session = el.find(utag + ['session-key']).text
    #sk = open(SESSIONKEY,"w")
    #sk.write(session_key)
except:
    print "no session-key found in reply"
if status != "1":
    error_str = SOAPCODES[status]
    raise Exception,error_str
    
if content_id is None:
    for stream in el.findall('*/' + utag + 'user-verified-content'):
        type = stream.find(utag + 'type').text
        if type == 'video':
            content_id = stream.find(utag + 'content-id').text
else:
    print "Using content_id from arguments: " + content_id
#for i in range(len(reply['user-verified-event'][0]['user-verified-content'][0]['domain-specific-attributes']['domain-attribute'])): 
#    print str(reply['user-verified-event'][0]['user-verified-content'][0]['domain-specific-attributes']['domain-attribute'][i]._name) + " = " + str(reply['user-verified-event'][0]['user-verified-content'][0]['domain-specific-attributes']['domain-attribute'][i])

#content_id = reply[0][0]['user-verified-content'][1]['content-id']
print "Event-id = " + str(event_id) + " and content-id = " + str(content_id)
#sys.exit()
#cmd_str = 'rm -rf /tmp/suds'
#subprocess.Popen(cmd_str,shell=True).wait()

#ip = client.factory.create('ns0:IdentityPoint')
#ip.__setitem__('identity-point-id', cookies['ipid'])
#ip.__setitem__('fingerprint', urllib.unquote(cookies['fprt']))

#pe = {'event-id':event_id, 'subject':'LIVE_EVENT_COVERAGE', 'playback-scenario':SCENARIO, 'content-id':content_id, 'fingerprint-identity-point':ip , 'session-key':session}


#try:
#    reply = client.service.find(**pe)
#except WebFault ,e:
#    print "WebFault received from content request:"
#    print e
#    sys.exit(1)

values = {
    'subject':'LIVE_EVENT_COVERAGE',
    'sessionKey': session,
    'identityPointId': cookies['ipid'],
    'contentId': content_id,
    'playbackScenario': SCENARIO,
    'eventId': event_id, 
    'fingerprint': urllib.unquote(cookies['fprt']),
}
theUrl = 'https://secure.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.1?' +\
    urllib.urlencode(values)
req = urllib2.Request(theUrl, None, txheaders);
response = urllib2.urlopen(req).read()
#print response
IL=0
xp = parseString(response)
printChildNodes(xp, IL)

#sys.exit()
el = xml.etree.ElementTree.XML(response)
utag = re.search('(\{.*\}).*', el.tag).group(1)
status = el.find(utag + 'status-code').text

if status != "1":
    error_str = SOAPCODES[status]
    raise Exception,error_str

#print reply[0][0]['user-verified-content'][0]['content-id']
#game_url = reply[0][0]['user-verified-content'][0]['user-verified-media-item'][0]['url'][0]
game_url = el.find('%suser-verified-event/%suser-verified-content/%suser-verified-media-item/%surl' %\
    (utag, utag, utag, utag)).text

print "DEBUG: FMS_CLOUD URL:\n"
print game_url
print "\n\n"
#sys.exit()

theurl = game_url
auth_pat = re.compile(r'auth=(.*)')
auth_chunk = re.search(auth_pat,game_url).groups()[0]
txheaders = {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13'}
data = None
req = urllib2.Request(theurl,data,txheaders)
response = urllib2.urlopen(req)
xp = parse(response)
rtmp_base = xp.getElementsByTagName('meta')[0].getAttribute('base')
for elem in xp.getElementsByTagName('video'):
    if elem.getAttribute('system-bitrate') == '1200000':
        vid_src = elem.getAttribute('src')
print "rtmp base = " + rtmp_base
print "vid src = " + vid_src
print "auth chunk = " + auth_chunk
game_url = rtmp_base + vid_src + '?auth=' + auth_chunk
print "from smil, game_url = "
print game_url
#sys.exit()

try:
    if play_path is None:
        #play_path_pat = re.compile(r'ondemand\/(.*)\?')
        play_path_pat = re.compile(r'ondemand(.*)$')
        play_path = re.search(play_path_pat,game_url).groups()[0]
        print "play_path = " + repr(play_path)
        app_pat = re.compile(r'ondemand(.*)\?(.*)$')
        app = "ondemand?_fcs_vhost=cp65670.edgefcs.net&akmfv=1.6"
        app += re.search(app_pat,game_url).groups()[1]
except:
    play_path = None
try:
    if play_path is None:
        live_sub_pat = re.compile(r'live\/mlb_c(.*)')
        sub_path = re.search(live_sub_pat,game_url).groups()[0]
        sub_path = 'mlb_c' + sub_path
        live_play_pat = re.compile(r'live\/mlb_c(.*)$')
        play_path = re.search(live_play_pat,game_url).groups()[0]
        play_path = 'mlb_c' + play_path
        if re.search('mlbsecurelive(.*)', game_url).groups() is not None:
            app = 'mlbsecurelive-live'
        else:
            app = "live?_fcs_vhost=cp65670.live.edgefcs.net&akmfv=1.6"
        bSubscribe = True
        
except:
    play_path = None
    sub_path = None

print "url = " + str(game_url)
print "play_path = " + str(play_path)
#sys.exit()

#sys.exit()
# End MORSEL extraction


theurl = 'http://cp65670.edgefcs.net/fcs/ident'
txheaders = {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13'}
data = None
req = urllib2.Request(theurl,data,txheaders)
response = urllib2.urlopen(req)
print response.read()
#sys.exit()

#print response.read()

#cmd_str = player + ' "' + game_url + '"'
recorder = datadct['video_recorder']
cmd_str = recorder.replace('%s', '"' + game_url + '"')
if play_path is not None:
    cmd_str += ' -y "' + play_path + '"'
if bSubscribe:
    cmd_str += ' -v -d "' + sub_path + '"'
if app is not None:
    cmd_str += ' -a "' + app + '"'
cmd_str += ' -o %e.mp4 '
cmd_str = cmd_str.replace('%e', event_id)
#cmd_str += ' | mplayer -really-quiet -cache 8192 -fs -'
try:
    print "\nplay_path = " + play_path
    print "\nsub_path  = " + sub_path
    print "\napp       = " + app
except:
    pass
print cmd_str + '\n'
#sys.exit()
playprocess = subprocess.Popen(cmd_str,shell=True)
playprocess.wait()

