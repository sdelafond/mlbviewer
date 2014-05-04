#!/usr/bin/env python

import urllib2, httplib
import StringIO
import gzip
import datetime
from mlbConstants import *

class MLBHttp:

    def __init__(self,accept_gzip=True):
        self.accept_gzip = accept_gzip
        self.opener = urllib2.build_opener()
        self.cache = dict()

    def getUrl(self,url):
        request = urllib2.Request(url)
        if self.accept_gzip:
            request.add_header('Accept-encoding', 'gzip')
        request.add_header('User-agent', USERAGENT)
        if self.cache.has_key(url):
            try:
                request.add_header('If-Modified-Since', self.cache[url]['last-modified'])
            except:
                pass
        else:
            self.cache[url] = dict()
        # for now, let errors drop through to the calling class
        try:
            rsp = self.opener.open(request)
        except urllib2.HTTPError, err:
            if err.code == 304:
                return self.cache[url]['response']
            else:
                raise
        self.cache[url]['last-modified'] = rsp.headers.get('Last-Modified')
        if rsp.headers.get('Content-Encoding') == 'gzip':
            compressedData = rsp.read()
            compressedStream = StringIO.StringIO(compressedData)
            gzipper = gzip.GzipFile(fileobj=compressedStream)
            self.cache[url]['response']= gzipper.read()
        else:
            self.cache[url]['response'] = rsp.read()
        return self.cache[url]['response']
    
