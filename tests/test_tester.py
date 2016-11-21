#!/usr/bin/env python

import unittest
import os
import sys
import random
import string
import jinja2
import collections
import urllib2

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

CONFIG_FILE = PARENT_DIR+ "/etc/urltester.conf"

sys.path.append(PARENT_DIR+"/lib/python")

import urltester.config
import urltester.tester

def random_string(size=10, chars=string.ascii_lowercase +string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class AssertCollectionMixin(object):
    def assertHasAttribute(self,obj,attribute,msg=None):
        if not msg:
            msg="%s has no attribute %s (type: %s)" % (unicode(obj),attribute,type(obj))
        if not hasattr(obj,attribute):
            self.fail(msg)

    def assertIsInteger(self,obj,msg=None):
        if not msg:
            msg="%s is not integer (type: %s)" % (unicode(obj),type(obj))
        if type(obj)==int: return
        self.fail(msg)

    def assertIsFloat(self,obj,msg=None):
        if not msg:
            msg="%s is not float (type: %s)" % (unicode(obj),type(obj))
        if type(obj)==float: return
        self.fail(msg)

    def assertIsString(self,obj,msg=None):
        if not msg:
            msg="%s is not string (type: %s)" % (unicode(obj),type(obj))
        if type(obj) in [str,unicode]: return
        self.fail(msg)

    def assertIsList(self,obj,msg=None):
        if not msg:
            msg="%s is not list (type: %s)" % (unicode(obj),type(obj))
        if type(obj) in [list]: return
        self.fail(msg)

    def assertIsDict(self,obj,msg=None):
        if not msg:
            msg="%s is not dict (type: %s)" % (unicode(obj),type(obj))
        if type(obj) in [dict]: return
        self.fail(msg)

    test_set=[PARENT_DIR+"/tests/real_test.conf"]
    test_proxy_host=""
    test_proxy_port=""


    def get_settings(self,**kwargs):
        kwargs["paths"]=self.test_set
        if self.test_proxy_host:
            kwargs["proxy_host"]=self.test_proxy_host
            kwargs["proxy_port"]=self.test_proxy_port
        settings=urltester.config.Settings(**kwargs)
        return settings

class TesterTest(unittest.TestCase,AssertCollectionMixin):

    test_set=[PARENT_DIR+"/tests/real_test_errori_ssl.conf",
              PARENT_DIR+"/tests/real_test_errori_socket.conf",
              PARENT_DIR+"/tests/real_test_corretti.conf"]

    def _check_test_response(self,test_response):
        self.assertIsInstance(test_response,urltester.tester.TestResponse)
        self.assertHasAttribute(test_response,"status")
        self.assertIsInteger(test_response.status)
        self.assertHasAttribute(test_response,"errno")
        self.assertIsInteger(test_response.errno)
        #self.assertEquals(test_response.status,200)
        self.assertHasAttribute(test_response,"time")
        self.assertIsFloat(test_response.time)
        self.assertHasAttribute(test_response,"msg")
        self.assertIsString(test_response.msg)

    def test_execution(self):
        settings=self.get_settings()
        for testname in settings.url_defs.keys():
            tester=urltester.tester.Tester(testname,settings.url_defs[testname].url,
                                           settings.url_defs[testname].timeout)
            test_response=tester.execute()
            self._check_test_response(test_response)
            print testname,test_response.status,test_response.time,test_response.msg,test_response.errno

    def test_manager_sequential(self):
        settings=self.get_settings()
        manager=urltester.tester.TestManager(settings)
        exec_time,response_dict=manager.run_sequential()
        print "Sequential:",exec_time
        self.assertIsInstance(response_dict,collections.OrderedDict)
        for testname in settings.url_defs.keys():
            self.assertIn(testname,response_dict.keys())
            test_response=response_dict[testname]["response"]
            self._check_test_response(test_response)
            print testname,test_response.status,test_response.time,test_response.msg,test_response.errno

    def test_manager_threaded(self):
        settings=self.get_settings()
        manager=urltester.tester.TestManager(settings)
        exec_time,response_dict=manager.run_threaded()
        print "Threaded:",exec_time
        self.assertIsInstance(response_dict,collections.OrderedDict)
        for testname in settings.url_defs.keys():
            self.assertIn(testname,response_dict.keys())
            test_response=response_dict[testname]["response"]
            self._check_test_response(test_response)
            print testname,test_response.status,test_response.time,test_response.msg,test_response.errno
            test_ok=response_dict[testname]["ok"]
            test_desc=response_dict[testname]["definition"]
            self.assertEqual(test_desc,settings.url_defs[testname])
            self.assertEqual(test_ok,settings.url_defs[testname].check_status(test_response.status))
            
class SSLTesterTest(TesterTest):
    test_set=[PARENT_DIR+"/tests/real_test_errori_ssl.conf"]
    
class SocketTesterTest(TesterTest):
    test_set=[PARENT_DIR+"/tests/real_test_errori_socket.conf"]
    
class OkTesterTest(TesterTest):
    test_set=[PARENT_DIR+"/tests/real_test_corretti.conf"]
    
class DefaultTesterTest(TesterTest):
    test_set=[PARENT_DIR+"/etc/urltester.conf"]
        
if __name__ == '__main__':  
    unittest.main()
