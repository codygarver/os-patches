#!/usr/bin/python3
# -*- Mode: Python; indent-tabs-mode: nil; tab-width: 4; coding: utf-8 -*-

import random
import logging
import multiprocessing
import os
import sys
try:
    from test.support import EnvironmentVarGuard
except ImportError:
    from test.test_support import EnvironmentVarGuard
import time
try:
    from urllib.error import HTTPError
    from urllib.request import install_opener, urlopen
except ImportError:
    from urllib2 import HTTPError, install_opener, urlopen
import unittest

try:
    from http.server import BaseHTTPRequestHandler
except ImportError:
    from BaseHTTPServer import BaseHTTPRequestHandler
try:
    from socketserver import TCPServer
except ImportError:
    from SocketServer import TCPServer

CURDIR = os.path.dirname(os.path.abspath(__file__))


class SillyProxyRequestHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        code = 200
        info = ""
        try:
            f = urlopen(self.path)
            info = f.info()
        except HTTPError as e:
            code = e.code
        s = "HTTP/1.0 %s OK\n%s" % (code, info)
        self.wfile.write(s.encode("UTF-8"))
    # well, good enough
    do_GET = do_HEAD


from UpdateManager.Core.MetaRelease import MetaReleaseCore, Dist


def get_new_dist(current_release):
    """
    common code to test new dist fetching, get the new dist information
    for hardy+1
    """
    meta = MetaReleaseCore()
    #meta.DEBUG = True
    meta.current_dist_name = current_release
    fake_metarelease = os.path.join(CURDIR, "test-data",
                                    "meta-release")
    meta.METARELEASE_URI = "file://%s" % fake_metarelease
    while meta.downloading:
        time.sleep(0.1)
    meta._buildMetaReleaseFile()
    meta.download()
    return meta.new_dist


class TestMetaReleaseCore(unittest.TestCase):

    def setUp(self):
        self.new_dist = None
        self.port = random.randint(1025, 65535)
        self.httpd = TCPServer(("", self.port), SillyProxyRequestHandler)
        self.httpd_process = multiprocessing.Process(
            target=self.httpd.serve_forever)
        self.httpd_process.start()

    def tearDown(self):
        self.httpd_process.terminate()
        self.httpd_process.join()
        install_opener(None)

    def testnewdist(self):
        """ test that upgrades offer the right upgrade path """
        for (current, next) in [("dapper", "edgy"),
                                ("hardy", "lucid"),
                                ("intrepid", "jaunty"),
                                ("jaunty", "karmic"),
                                ("karmic", "lucid")]:
            new_dist = get_new_dist(current)
            self.assertEqual(next, new_dist.name,
                             "New dist name for %s is '%s', "
                             "but expected '%s''" % (current, new_dist.name,
                                                     next))

    def test_url_downloadable(self):
        from UpdateManager.Core.utils import url_downloadable
        with EnvironmentVarGuard() as environ:
            logging.debug("proxy 1")
            environ["http_proxy"] = "http://localhost:%s/" % self.port
            install_opener(None)
            self.assertTrue(url_downloadable("http://www.ubuntu.com/desktop",
                                             logging.debug),
                            "download with proxy %s failed" %
                            environ["http_proxy"])
            logging.debug("proxy 2")
            environ["http_proxy"] = "http://localhost:%s" % self.port
            install_opener(None)
            self.assertTrue(url_downloadable("http://www.ubuntu.com/desktop",
                            logging.debug),
                            "download with proxy %s failed" %
                            environ["http_proxy"])
            logging.debug("no proxy")
            del environ["http_proxy"]
            install_opener(None)
            self.assertTrue(url_downloadable("http://www.ubuntu.com/desktop",
                            logging.debug),
                            "download with no proxy failed")

            logging.debug("no proxy, no valid adress")
            self.assertFalse(url_downloadable("http://www.ubuntu.com/xxx",
                                              logging.debug),
                             "download with no proxy failed")

            logging.debug("proxy, no valid adress")
            environ["http_proxy"] = "http://localhost:%s" % self.port
            install_opener(None)
            self.assertFalse(url_downloadable("http://www.ubuntu.com/xxx",
                                              logging.debug),
                             "download with no proxy failed")

    def test_get_uri_query_string(self):
        # test with fake data
        d = Dist("oneiric", "11.10", "2011-10-10", True)
        meta = MetaReleaseCore()
        q = meta._get_release_notes_uri_query_string(d)
        self.assertTrue("os=ubuntu" in q)
        self.assertTrue("ver=11.10" in q)

    def test_html_uri_real(self):
        with EnvironmentVarGuard() as environ:
            environ["META_RELEASE_FAKE_CODENAME"] = "lucid"
            # useDevelopmentRelease=True is only needed until precise is
            # released
            meta = MetaReleaseCore(forceDownload=True, forceLTS=True,
                                   useDevelopmentRelease=True)
            while meta.downloading:
                time.sleep(0.1)
            self.assertIsNotNone(meta.new_dist)
            uri = meta.new_dist.releaseNotesHtmlUri
            f = urlopen(uri)
            data = f.read().decode("UTF-8")
            self.assertTrue(len(data) > 0)
            self.assertTrue("<html>" in data)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "-v":
        logging.basicConfig(level=logging.DEBUG)
    unittest.main()
