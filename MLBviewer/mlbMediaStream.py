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
import subprocess
import select

from copy import deepcopy
from xml.dom.minidom import parse
import xml.dom.minidom

from mlbProcess import MLBprocess
from mlbError import *
from mlbConstants import *
from mlbLog import MLBLog
from mlbConfig import MLBConfig

class MediaStream:

    def __init__(self, stream, session, cfg, coverage=None, 
                 streamtype='video', start_time=0):
        # Initialize basic object from instance variables
        self.stream = stream
	self.session = session
        self.cfg = cfg
        if coverage == None:
            self.coverage = 0
        else:
            self.coverage = coverage
        self.start_time = start_time
        self.streamtype = streamtype

        # Need a few config items
        self.use_nexdef    = self.cfg.get('use_nexdef')
        self.postseason    = self.cfg.get('postseason')
        self.use_librtmp   = self.cfg.get('use_librtmp')
        self.use_wired_web = self.cfg.get('use_wired_web')
        self.max_bps       = int(self.cfg.get('max_bps'))
        self.min_bps       = int(self.cfg.get('min_bps'))
        # allow max_bps and min_bps to be specified in kbps
        if self.min_bps < 128000:
            self.min_bps *= 1000
        if self.max_bps < 128000:
            self.max_bps *= 1000
        self.speed         = self.cfg.get('speed')
        self.adaptive      = self.cfg.get('adaptive_stream')

       
        # Install the cookie received from MLBLogin and used for subsequent 
        # media requests.  This part should resolve the issue of login 
        # restriction errors when each MediaStream request was its own login/
        # logout sequence.
        try:
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.session.cookie_jar))
            urllib2.install_opener(opener)
        except:
            raise

        self.log = MLBLog(LOGFILE)
        self.error_str = "What happened here?\nPlease enable debug with the d key and try your request again."

        # Break the stream argument into its components used for media location
        # requests.
        try:
            ( self.call_letters,
              self.team_id,
              self.content_id,
              self.event_id ) = self.stream
        except:
            self.error_str = "No stream available for selected game."

        self.log.write(str(datetime.datetime.now()) + '\n')
        try:
            self.session_key = self.session.session_key
        except:
            self.session_key = None
        self.debug = cfg.get('debug')

        # The request format depends on the streamtype
        if self.streamtype == 'audio':
            self.scenario = "AUDIO_FMS_32K"
            self.subject  = "MLBCOM_GAMEDAY_AUDIO"
        else:
            if self.use_nexdef:
                if self.use_wired_web:
                    self.scenario = 'HTTP_CLOUD_WIRED_WEB'
                else:
                    self.scenario = 'HTTP_CLOUD_WIRED'
            else:
                self.scenario = 'FMS_CLOUD'
            #self.subject  = "LIVE_EVENT_COVERAGE"
            self.subject = "MLBTV"

        # Media response needs to be parsed into components below.
        self.auth_chunk = None
        self.play_path = None
        self.tc_url = None
        self.app = None
        self.rtmp_url = None
        self.rtmp_host = None
        self.rtmp_port = None
        self.sub_path = None

        # TODO: Has this findUserVerifiedEvent been updated?  Does this 
        # url need to be changed to reflect that?
        self.base_url='https://secure.mlb.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.3?' 


    def createMediaRequest(self,stream):
        if stream == None:
            self.error_str = "No event-id present to create media request."
            raise

        try:
            #sessionKey = urllib.unquote(self.session.cookies['ftmu'])
            sessionKey = self.session.session_key
        except:
            sessionKey = None
      
        # Query values
        query_values = {
            'eventId': self.event_id,
            'sessionKey': sessionKey,
            'fingerprint': urllib.unquote(self.session.cookies['fprt']),
            'identityPointId': self.session.cookies['ipid'],
            'playbackScenario': self.scenario,
            'subject': self.subject
        }
        # Build query
        url = self.base_url + urllib.urlencode(query_values)
        
        # And make the request
        req = urllib2.Request(url)
        try:
            response = urllib2.urlopen(req)
        except urllib2.HTTPError, err:
            self.log.write("Error (%s) for URL: %s" % ( err.code, url ))
            raise
        reply = xml.dom.minidom.parse(response)
        return reply

    def locateMedia(self):
        if self.streamtype == 'condensed':
            return self.locateCondensedMedia()
        game_url = None
        # 1. Make initial media request -- receive a reply with available media
        # 2. Update the session with current cookie values/session key.
        # 3. Get the content_list that matches the requested stream
        # 4. Strip out blacked out content or content that is not authorized.

        # if no user=, don't even attempt media requests for non-free
        # media
        if self.cfg.get('user') == "" or self.cfg.get('user') is None:
            self.error_str = 'MLB.TV subscription is required for this media.'
            raise MLBAuthError,self.error_str
        reply = self.createMediaRequest(self.stream)
        self.updateSession(reply)
        content_list = self.parseMediaReply(reply)
        game_url = self.requestSpecificMedia()
        return game_url


    def updateSession(self,reply):
        try:
            self.session_key = reply.getElementsByTagName('session-key')[0].childNodes[0].data
            self.session.session_key = self.session_key
            self.session_keys['ftmu'] = self.session_key
            self.session.writeSessionKey(self.session_key)
        except:
            pass


    def parseMediaReply(self,reply):
        
        # If status is not successful, make it easier to determine why
        status_code = str(reply.getElementsByTagName('status-code')[0].childNodes[0].data)
        if status_code != "1":
            self.log.write("UNSUCCESSFUL MEDIA REQUEST: status-code: %s , event-id = %s\n" % (status_code , self.event_id))
            self.log.write("See %s for XML response.\n"%ERRORLOG_1)
            err1 = open(ERRORLOG_1, 'w')
            reply.writexml(err1)
            err1.close()
            self.error_str = SOAPCODES[status_code]
            raise Exception,self.error_str
        else:
            self.log.write("SUCCESSFUL MEDIA REQUEST: status-code: %s , event-id = %s\n" % (status_code , self.event_id))
            self.log.write("See %s for XML response.\n"%MEDIALOG_1)
            med1 = open(MEDIALOG_1,'w')
            reply.writexml(med1)
            med1.close()

        # determine blackout status
        self.determineBlackoutStatus(reply)

        # and now the meat of the parsing...
        content_list = []

        for content in reply.getElementsByTagName('user-verified-content'):
            type = content.getElementsByTagName('type')[0].childNodes[0].data
            if type != self.streamtype:
               continue
            content_id = content.getElementsByTagName('content-id')[0].childNodes[0].data
            if content_id != self.content_id:
                continue

            # First, collect all the domain-attributes
            dict = {}

            for node in content.getElementsByTagName('domain-attribute'):
                name = str(node.getAttribute('name'))
                value = node.childNodes[0].data
                dict[name] = value
            # There are a series of checks to trim the content list
            # 1. Trim out 'in-market' listings like Yankees On Yes
            if dict.has_key('coverage_type'):
                if 'in-market' in dict['coverage_type']:
                    continue
            # 2. Trim out all non-English language broadcasts
            if dict.has_key('language'):
                if dict['language'] != 'EN':
                    continue
            # 3. For post-season, trim out multi-angle listings
            if self.cfg.get('postseason'):
                if dict['in_epg'] != 'mlb_multiangle_epg':
                    continue
            else:
                if dict['in_epg'] == 'mlb_multiangle_epg':
                    continue
            # 4. Get coverage association and call_letters
            try:
                cov_pat = re.compile(r'([0-9][0-9]*)')
                coverage = re.search(cov_pat, dict['coverage_association']).groups()[0]
            except:
                 coverage = None
            try:
                call_letters = dict['call_letters']
            except:
                if self.cfg.get('postseason') == False:
                    raise Exception,repr(dict)
                else:
                    call_letters = 'MLB'
            for media in content.getElementsByTagName('user-verified-media-item'):
                state = media.getElementsByTagName('state')[0].childNodes[0].data
                scenario = media.getElementsByTagName('playback-scenario')[0].childNodes[0].data
                if scenario == self.scenario and \
                    state in ('MEDIA_ARCHIVE', 'MEDIA_ON', 'MEDIA_OFF'):
                    content_list.append( ( call_letters, coverage, content_id, self.event_id ) )
        return content_list
 

    def determineBlackoutStatus(self,reply):
        # Determine the blackout status
        try:
            blackout_status = reply.getElementsByTagName('blackout')[0].childNodes[0].data
        except:
            blackout_status = reply.getElementsByTagName('blackout-status')[0]
            try:
                success_status = blackout_status.getElementsByTagName('successStatus')
                blackout_status = None
            except:
                try:
                    location_status = blackout_status.getElementsByTagName('locationCannotBeDeterminedStatus')
                except:
                    blackout_status = 'LOCATION CANNOT BE DETERMINED.'

        media_type = reply.getElementsByTagName('type')[0].childNodes[0].data
        media_state = reply.getElementsByTagName('state')[0].childNodes[0].data
        self.media_state = media_state
      
        if blackout_status is not None and self.streamtype == 'video':
            inmarket_pat = re.compile(r'INMARKET')
            if re.search(inmarket_pat,blackout_status) is not None:
                pass
            elif media_state == 'MEDIA_ON' and not self.postseason:
                self.log.write('MEDIA STREAM BLACKOUT.  See %s for XML response.' % BLACKFILE)
                self.error_str = 'BLACKOUT: ' + str(blackout_status)
                bf = open(BLACKFILE, 'w')
                reply.writexml(bf)
                bf.close()
                raise Exception,self.error_str

    def selectCoverage(self,content_list):
        # now iterate over the content_list with the following rules:
        # 1. if coverage association is zero, use it (likely a national broadcast)
        # 2. if preferred coverage is available use it
        # 3. if coverage association is non-zero and preferred not available, then what?
        for content in content_list:
            ( call_letters, coverage, content_id , event_id ) = content
            if coverage == '0':
                self.content_id = content_id
                self.call_letters = call_letters
            elif coverage == self.coverage:
                self.content_id = content_id
                self.call_letters = call_letters
        # if we preferred coverage and national coverage not available,
        # select any coverage available
        if self.content_id is None:
            try:
                ( call_letters, coverage, content_id, event_id ) = content_list[0]
                self.content_id = content_id
                self.call_letters = call_letters
            except:
                self.content_id = None
                self.call_letters = None
        if self.content_id is None:
            self.error_str = "Requested stream is not available."
            self.error_str += "\n\nRequested coverage association: " + str(self.coverage)
            self.error_str += "\n\nAvailable content list = \n" + repr(content_list)
            raise Exception,self.error_str
        if self.debug:
            self.log.write("DEBUG>> writing soap response\n")
            self.log.write(repr(reply) + '\n')
        if self.content_id is None:
            self.error_str = "Requested stream is not yet available."
            raise Exception,self.error_str
        if self.debug:
            self.log.write("DEBUG>> soap event-id:" + str(self.stream) + '\n')
            self.log.write("DEBUG>> soap content-id:" + str(self.content_id) + '\n')

    def requestSpecificMedia(self):
        try:
            #sessionkey = urllib.unquote(self.session.cookies['ftmu'])
            sessionKey = self.session.session_key
        except:
            sessionKey = None
        query_values = {
            'subject': self.subject,
            'sessionKey': sessionKey,
            'identityPointId': self.session.cookies['ipid'],
            'contentId': self.content_id,
            'playbackScenario': self.scenario,
            'eventId': self.event_id,
            'fingerprint': urllib.unquote(self.session.cookies['fprt'])
        }
        url = self.base_url + urllib.urlencode(query_values)
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        reply = parse(response)

        status_code = str(reply.getElementsByTagName('status-code')[0].childNodes[0].data)
        if status_code != "1":
            # candidate for new procedure: this code block of writing
            # unsuccessful xml responses is being repeated...
            self.log.write("DEBUG (SOAPCODES!=1)>> writing unsuccessful soap response event_id = " + str(self.event_id) + " contend-id = " + self.content_id + "\n")
            df = open('/tmp/unsuccessful.xml','w')
            reply.writexml(df)
            df.close()
            df = open('/tmp/unsuccessful.xml')
            msg = df.read()
            df.close()
            self.error_str = SOAPCODES[status_code]
            raise Exception,self.error_str
        try:
            self.session_key = reply.getElementsByTagName('session-key')[0].childNodes[0].data
            self.session.cookies['ftmu'] = self.session_key
            self.session.writeSessionKey(self.session_key)
        except:
            #raise
            self.session_key = None
        try:
            game_url = reply.getElementsByTagName('url')[0].childNodes[0].data
        except:
            self.error_str = "Stream URL not found in reply.  Stream may not be available yet."
            # check for notAuthorizedStatus
            try:
                authStatus = reply.getElementsByTagName('auth-status')[0].childNodes[0].nodeName
                if authStatus == 'notAuthorizedStatus':
                    self.error_str = "Media response contained a notAuthorizedStatus."
            except:
                pass
            df = open(ERRORLOG_2,'w')
            reply.writexml(df)
            df.close()
            raise Exception,self.error_str
        else:
            df = open(MEDIALOG_2,'w')
            reply.writexml(df)
            df.close()
        self.log.write("DEBUG>> URL received: " + game_url + '\n')
        return game_url


    def parseFmsCloudResponse(self,url):
        auth_pat = re.compile(r'auth=(.*)')
        self.auth_chunk = '?auth=' + re.search(auth_pat,url).groups()[0]
        out = ''
        try:
            req = urllib2.Request(url)
            handle = urllib2.urlopen(req)
        except:
            self.error_str = \
"An error occurred in the final request.\nThis is not a blackout or a media location error.\n\n\nIf the problem persists, try the non-Nexdef stream."
            raise Exception,self.error_str
        rsp = parse(handle)
        mlog = open(FMSLOG, 'w')
        rsp.writexml(mlog)
        mlog.close()
        rtmp_base = rsp.getElementsByTagName('meta')[0].getAttribute('base')
        for elem in rsp.getElementsByTagName('video'):
            try:
                speed = int(elem.getAttribute('system-bitrate'))/1000
            except ValueError:
                continue
            if int(self.speed) == int(speed):
               #vid_src = elem.getAttribute('src').replace('mp4:','/')
               vid_src = elem.getAttribute('src')
               out = rtmp_base + vid_src + self.auth_chunk
        return out


    def prepareMediaStreamer(self,game_url):
        if self.streamtype == 'condensed':
            if self.cfg.get('use_librtmp'):
                return self.prepareFmsUrl(game_url)
            else:
                return 'rtmpdump -o - -r %s' % game_url
        elif self.streamtype == 'classics':
            return 'youtube-dl -o - \'%s\'' % game_url
        elif self.cfg.get('use_nexdef') and self.streamtype != 'audio':
            self.nexdef_media_url = game_url
            return self.prepareHlsCmd(game_url)
        else:
            if self.streamtype in ( 'video', ):
                game_url = self.parseFmsCloudResponse(game_url)
            return self.prepareFmsUrl(game_url)


    # finally some url processing routines
    def prepareFmsUrl(self,game_url):
        try:
            play_path_pat = re.compile(r'ondemand(.*)$')
            #play_path_pat = re.compile(r'ondemand\/(.*)$')
            self.play_path = re.search(play_path_pat,game_url).groups()[0]
            app_pat = re.compile(r'ondemand(.*)\?(.*)$')
            querystring = re.search(app_pat,game_url).groups()[1]
            self.app = "ondemand?_fcs_vhost=cp65670.edgefcs.net&akmfv=1.6" + querystring
            # not sure if we need this
            try:
                req = urllib2.Request('http://cp65670.edgefcs.net/fcs/ident')
                page = urllib2.urlopen(req)
                fp = parse(page)
                ip = fp.getElementsByTagName('ip')[0].childNodes[0].data
                self.tc_url = 'http://' + str(ip) + ':1935/' + self.app
            except:
                self.tc_url = None
        except:
            self.play_path = None
        try:
            live_pat = re.compile(r'live\/mlb')
            if re.search(live_pat,game_url):
                if self.streamtype == 'audio':
                    auth_pat = re.compile(r'auth=(.*)')
                    self.auth_chunk = '?auth=' + re.search(auth_pat,game_url).groups()[0]
                    live_sub_pat = re.compile(r'live\/mlb_audio(.*)\?')
                    self.sub_path = re.search(live_sub_pat,game_url).groups()[0]
                    self.sub_path = 'mlb_audio' + self.sub_path
                    live_play_pat = re.compile(r'live\/mlb_audio(.*)$')
                    self.play_path = re.search(live_play_pat,game_url).groups()[0]
                    self.play_path = 'mlb_audio' + self.play_path
                    app_auth = self.auth_chunk.replace('?','&')
                    self.app = "live?_fcs_vhost=cp153281.live.edgefcs.net&akmfv=1.6&aifp=v0006" + app_auth
                else:
                    try:
                        live_sub_pat = re.compile(r'live\/mlb_c(.*)')
                        self.sub_path = re.search(live_sub_pat,game_url).groups()[0]
                        #self.sub_path = 'mlb_c' + self.sub_path + self.auth_chunk
                        self.sub_path = 'mlb_c' + self.sub_path
                        self.sub_path = self.sub_path.replace(self.auth_chunk,'')
                    except Exception,detail:
                        self.error_str = 'Could not parse the stream subscribe path: ' + str(detail)
                        raise Exception,self.error_str
                    else:
                        game_url = game_url.replace(self.auth_chunk,'')
                    try:
                        live_path_pat = re.compile(r'live\/mlb_c(.*)$')
                        self.play_path = re.search(live_path_pat,game_url).groups()[0]
                        self.play_path = 'mlb_c' + self.play_path + self.auth_chunk
                    except Exception,detail:
                        self.error_str = 'Could not parse the stream play path: ' + str(detail)
                        raise Exception,self.error_str
                    sec_pat = re.compile(r'mlbsecurelive')
                    if re.search(sec_pat,game_url) is not None:
                        self.app = 'mlbsecurelive-live'
                    else:
                        self.app = 'live?_fcs_vhost=cp65670.live.edgefcs.net&akmfv=1.6'
            if self.debug:
                self.log.write("DEBUG>> sub_path = " + str(self.sub_path) + "\n")
                self.log.write("DEBUG>> play_path = " + str(self.play_path) + "\n")
                self.log.write("DEBUG>> app = " + str(self.app) + "\n")
        except Exception,e:
            self.error_str = str(e)
            raise Exception,e
            #raise Exception,game_url
            self.app = None
        if self.debug:
            self.log.write("DEBUG>> soap url = \n" + str(game_url) + '\n')
        self.log.write("DEBUG>> soap url = \n" + str(game_url) + '\n')

        self.filename = os.path.join(os.environ['HOME'], 'mlbdvr_games')
        self.filename += '/' + str(self.event_id)
        if self.streamtype == 'audio':
            self.filename += '.mp3'
        else:
            self.filename += '.mp4'
        recorder = DEFAULT_F_RECORD
        if self.use_librtmp:
            self.rec_cmd_str = self.prepareLibrtmpCmd(recorder,self.filename,game_url)
        else:
            self.rec_cmd_str = self.prepareRtmpdumpCmd(recorder,self.filename,game_url)
        return self.rec_cmd_str

    def prepareHlsCmd(self,streamUrl):
        self.hd_str = DEFAULT_HD_PLAYER
        self.hd_str = self.hd_str.replace('%B', streamUrl)
        #self.hd_str = self.hd_str.replace('%P', str(self.max_bps))
        if self.adaptive:
            self.hd_str += ' -b ' + str(self.max_bps)
            self.hd_str += ' -s ' + str(self.min_bps)
            self.hd_str += ' -m ' + str(self.min_bps)
        else:
            self.hd_str += ' -L'
            self.hd_str += ' -s ' + str(self.max_bps)
        if self.media_state != 'MEDIA_ON' and self.start_time is None:
            self.hd_str += ' -f ' + str(HD_ARCHIVE_OFFSET)
        elif self.start_time is not None:
            # handle inning code here (if argument changes, here is where it
            # needs to be updated.
            self.hd_str += ' -F ' + str(self.start_time)
        self.hd_str += ' -o -'
        return self.hd_str

    def prepareRtmpdumpCmd(self,rec_cmd_str,filename,streamurl):
        # remove short files
        try:
            filesize = long(os.path.getsize(filename))
        except:
            filesize = 0
        if filesize <= 5:
            try:
                os.remove(filename)
                self.log.write('\nRemoved short file: ' + str(filename) + '\n')
            except:
                pass

        #rec_cmd_str = rec_cmd_str.replace('%f', filename)
        rec_cmd_str = rec_cmd_str.replace('%f', '-')
        rec_cmd_str = rec_cmd_str.replace('%s', '"' + streamurl + '"')
        if self.play_path is not None:
            rec_cmd_str += ' -y "' + str(self.play_path) + '"'
        if self.app is not None:
            rec_cmd_str += ' -a "' + str(self.app) + '"'
        rec_cmd_str += ' -s http://mlb.mlb.com/flash/mediaplayer/v4/RC91/MediaPlayer4.swf?v=4'
        if self.tc_url is not None:
            rec_cmd_str += ' -t "' + self.tc_url + '"'
        if self.sub_path is not None:
            rec_cmd_str += ' -d "' + str(self.sub_path) + '" -v'
        if self.rtmp_host is not None:
            rec_cmd_str += ' -n ' + str(self.rtmp_host)
        if self.rtmp_port is not None:
            rec_cmd_str += ' -c ' + str(self.rtmp_port)
        if self.start_time is not None and self.streamtype != 'audio':
            if self.use_nexdef == False:
                rec_cmd_str += ' -A ' + str(self.start_time)
        self.log.write("\nDEBUG>> rec_cmd_str" + '\n' + rec_cmd_str + '\n\n')
        return rec_cmd_str

    def prepareLibrtmpCmd(self,rec_cmd_str,filename,streamurl):
        mplayer_str = '"' + streamurl
        if self.play_path is not None:
            mplayer_str += ' playpath=' + self.play_path
        if self.app is not None:
            if self.sub_path is not None:
                mplayer_str += ' app=' + self.app
                mplayer_str += ' subscribe=' + self.sub_path + ' live=1'
            else:
                mplayer_str += ' app=' + self.app
        mplayer_str += '"'
        self.log.write("\nDEBUG>> mplayer_str" + '\n' + mplayer_str + '\n\n')
        return mplayer_str

    def preparePlayerCmd(self,media_url,gameid,streamtype='video'):
        if streamtype == 'video':
            player = self.cfg.get('video_player')
        elif streamtype == 'audio':
            player = self.cfg.get('audio_player')
        elif streamtype in ('highlight', 'condensed', 'classics'):
            player = self.cfg.get('top_plays_player')
            if player == '':
                player = self.cfg.get('video_player')
        if '%s' in player:
            if streamtype == 'video' and self.cfg.get('use_nexdef'):
                cmd_str = player.replace('%s', '-')
                cmd_str  = media_url + ' | ' + cmd_str
            elif self.cfg.get('use_librtmp') or streamtype == 'highlight':
                cmd_str = player.replace('%s', media_url)
            else:
                cmd_str = player.replace('%s', '-')
                cmd_str  = media_url + ' | ' + cmd_str
        else:
            if streamtype == 'video' and self.cfg.get('use_nexdef'):
                cmd_str = media_url + ' | ' + player + ' - '
            elif self.cfg.get('use_librtmp') or streamtype == 'highlight':
                cmd_str = player + ' ' + media_url
            else:
                cmd_str = media_url + ' | ' + player + ' - '
        if '%f' in player:
            fname = self.prepareFilename(gameid)
            cmd_str = cmd_str.replace('%f', fname)
        return cmd_str

    # Still uncertain where recording falls in ToS but at least can give
    # more options on filename if that's the route some will take.
    def prepareFilename(self,gameid):
        filename_format = self.cfg.get('filename_format')
        gameid = gameid.replace('/','-')
        if filename_format is not None and filename_format != "":
            fname = filename_format
        else:
            if self.cfg.get('milbtv'):
                # call letters is always blank for milbtv
                fname = '%g.%m'
            else:
                fname = '%g-%l.%m'
        # Supported_tokens =  ( '%g', gameid, e.g. 2013-05-28-slnmlb-kcamlb-1
        #                       '%l', call_letters, e.g. FSKC-HD
        #                       '%t', team_id, e.g. 118 (mostly useless)
        #                       '%c', content_id, e.g. 27310673
        #                       '%e', event_id, e.g. 14-347519-2013-05-28
        #                       '%m', suffix, e.g. 'mp3' or 'mp4')
        # Default format above would translate to: 
        # 2013-05-28-slnmlb-kcamlb-1-FSKC-HD.mp4
        fname = fname.replace('%g',gameid)
        if self.cfg.get('milbtv'):
            # if call letters are really desired, make some up ;)
            fname = fname.replace('%l', 'MiLB')
        else:
            fname = fname.replace('%l',self.stream[0])
        # team is 0 for condensed, coerce it to str
        fname = fname.replace('%t',str(self.stream[1]))
        fname = fname.replace('%c',self.stream[2])
        fname = fname.replace('%e',self.stream[3])
        if self.streamtype == 'audio':
            suffix = 'mp3'
        else:
            suffix = 'mp4'
        if fname.find('%m') < 0:
            fname = fname + '.%s' % suffix
        else:
            fname = fname.replace('%m', suffix)
        return fname

    def locateCondensedMedia(self):
        self.streamtype = 'condensed'
        cvUrl = 'http://mlb.mlb.com/gen/multimedia/detail/'
        cvUrl += self.content_id[-3] + '/' + self.content_id[-2] + '/' + self.content_id[-1]
        cvUrl += '/' + self.content_id + '.xml'
        try:
            req = urllib2.Request(cvUrl)
            rsp = urllib2.urlopen(req)
        except Exception,detail:
            self.error_str = 'Error while locating condensed game:'
            self.error_str = '\n\n' + str(detail)
            self.log.write('locateCondensedMedia: %s\n' % cvUrl)
            self.log.write(str(detail))
            raise Exception,self.error_str
        try:
            media = parse(rsp)
        except Exception,detail:
            self.error_str = 'Error parsing condensed game location'
            self.error_str += '\n\n' + str(detail)
            self.log.write('locateCondensedMedia: %s\n' % cvUrl)
            self.log.write(str(detail))
            raise Exception,self.error_str
        if int(self.cfg.get('speed')) >= 1800:
            playback_scenario = 'FLASH_1800K_960X540'
        else:
            playback_scenario = 'FLASH_1200K_640X360'
        for url in media.getElementsByTagName('url'):
            if url.getAttribute('playback_scenario') == playback_scenario:

                condensed = str(url.childNodes[0].data)
        try:
            condensed
        except:
            self.error_str = 'Error parsing condensed video reply. See %s for XML response.\n' % ERRORLOG_1
            self.log.write('locateCondensedMedia(): requested url:\n')
            self.log.write('%s\n' % cvUrl)
            self.log.write(self.error_str)
            mlog = open(ERRORLOG_1,'w')
            media.writexml(mlog)
            mlog.close()
            raise Exception,self.error_str
        self.log.write('locateCondensedMedia(): requested url:\n')
        self.log.write('%s\n' % cvUrl)
        mlog = open(MEDIALOG_1, 'w')
        media.writexml(mlog)
        mlog.close()
        self.log.write('Wrote raw XML reply to %s\n' % MEDIALOG_1)
        return condensed

