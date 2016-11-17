#!/usr/bin/env python

import os
import urllib2
import unittest
import string
import random
import sys

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
sys.path.append(PARENT_DIR+"/lib/python")

import urltester.config

def random_string(size=10, chars=string.ascii_lowercase +string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class MyHttpErrorsHandler(urllib2.BaseHandler):

    def http_error_404(self,req, fp, code, msg, hdrs):
        return fp

class UrllibPageTest(object):
    base_title="UrlTester"

    def __init__(self,url,status,msg,headers):
        self.url=url
        self.status=status
        self.msg=msg
        self.headers=headers

    def __call__(self,cls):
        opener = urllib2.build_opener(MyHttpErrorsHandler())
        urllib2.install_opener(opener)

        f=urllib2.urlopen(self.url,timeout=2)
        f.close()
        cls.assertEquals(f.code,self.status)
        cls.assertEquals(f.msg,self.msg)
        for k in self.headers.keys():
            cls.assertIn(k.lower(),map(lambda x: x.lower(),f.headers.keys()))
            cls.assertEquals(self.headers[k].lower(),f.headers[k].lower())
        
class UrllibTestMixin(object):
    base_url="http://localhost:9876"
    base_headers={
        'content-type':'text/html; charset=utf-8'
    }

    def setUp(self):  
        pass

    def tearDown(self):  
        pass

class UrllibTest(unittest.TestCase,UrllibTestMixin):
    def setUp(self):  
        UrllibTestMixin.setUp(self)

    def tearDown(self):  
        UrllibTestMixin.tearDown(self)

class UrllibTestConfigUrls(unittest.TestCase,UrllibTestMixin):
    def setUp(self): 
        pass

    def tearDown(self): 
        pass
    
    def test_base_url(self):
        headers=self.base_headers
        ptest=UrllibPageTest(self.base_url,200,"OK",headers)
        ptest(self)
        ptest=UrllibPageTest(self.base_url+"/",200,"OK",headers)
        ptest(self)

    def test_environ(self):
        headers=self.base_headers
        ptest=UrllibPageTest(self.base_url+"/environ",200,"OK",headers)
        ptest(self)
        ptest=UrllibPageTest(self.base_url+"/environ/",200,"OK",headers)
        ptest(self)
        
    def test_config(self):
        headers=self.base_headers
        ptest=UrllibPageTest(self.base_url+"/config",200,"OK",headers)
        ptest(self)
        ptest=UrllibPageTest(self.base_url+"/config/",200,"OK",headers)
        ptest(self)

    def test_urls_defs(self):
        headers=self.base_headers
        settings=urltester.config.Settings()
        for testurl in settings.url_defs.keys():
            ptest=UrllibPageTest(self.base_url+"/"+testurl,200,"OK",headers)
            ptest(self)
            ptest=UrllibPageTest(self.base_url+"/"+testurl+"/",200,"OK",headers)
            ptest(self)

    def test_random(self):
        headers=self.base_headers
        settings=urltester.config.Settings()
        for iteration in range(0,10):
            L=random.choice(range(1,50))
            testurl=random_string(L)
            while testurl in [ "environ","config" ]+settings.url_defs.keys(): testurl=random_string(L)
            ptest=UrllibPageTest(self.base_url+"/"+testurl,404,"Not Found",headers)
            ptest(self)
            ptest=UrllibPageTest(self.base_url+"/"+testurl+"/",404,"Not Found",headers)
            ptest(self)

if __name__ == '__main__':  
    unittest.main()
