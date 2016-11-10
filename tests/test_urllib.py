#!/usr/bin/python

import os
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import unittest

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

class UrllibPageTest(object):
    base_title="UrlTester"

    def __init__(self,url):
        self.url=url

    def __call__(self,cls):
        f=urllib2.urlopen(self.url,timeout=2)
        print f.read()
        
class UrllibTestMixin(object):
    base_url="http://localhost:9876"

    def setUp(self):  
        pass

    def tearDown(self):  
        pass

    def test_base_url(self):
        ptest=UrllibPageTest(self.base_url)
        ptest(self)

class UrllibTest(unittest.TestCase,UrllibTestMixin):
    def setUp(self):  
        UrllibTestMixin.setUp(self)

    def tearDown(self):  
        UrllibTestMixin.tearDown(self)

if __name__ == '__main__':  
    unittest.main()
