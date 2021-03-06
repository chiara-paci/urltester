#!/usr/bin/env python

import os
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import unittest

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
# DB_DIR     = os.path.join( os.path.join(PARENT_DIR, 'var'), 'databases' )

GECKODRIVER_BIN = os.path.join( PARENT_DIR, 'bin' )
FIREFOX_PATH = "/usr/local/firefox/firefox"
os.environ["PATH"]+=":"+GECKODRIVER_BIN

class SeleniumPageTest(object):
    base_title="UrlTester"

    def __init__(self,url):
        self.url=url

    def __call__(self,cls):
        cls.browser.get(self.url)
        cls.assertIn(self.base_title,cls.browser.title)

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
    
        
class SeleniumTestMixin(object):
    base_url="http://localhost:9876"

    def setUp(self):  
        self.browser = webdriver.Firefox(firefox_binary=FirefoxBinary(firefox_path=FIREFOX_PATH))
        self.browser.implicitly_wait(10)

    def tearDown(self):  
        self.browser.quit()

    def test_base_url(self):
        ptest=SeleniumPageTest(self.base_url)
        ptest(self)

class SeleniumTest(unittest.TestCase,SeleniumTestMixin):
    def setUp(self):  
        SeleniumTestMixin.setUp(self)

    def tearDown(self):  
        SeleniumTestMixin.tearDown(self)


class UrllibTest(unittest.TestCase,UrllibTestMixin):
    def setUp(self):  
        UrllibTestMixin.setUp(self)

    def tearDown(self):  
        UrllibTestMixin.tearDown(self)

if __name__ == '__main__':  
    unittest.main()
