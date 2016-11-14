#!/usr/bin/python

import unittest
import os
import sys
import random
import string
import jinja2

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

CONFIG_FILE = PARENT_DIR+ "/etc/urltester.conf"

sys.path.append(PARENT_DIR+"/lib/python")

import urltester.config
import urltester.server

def apply_template(settings,template_name,context):
    env=jinja2.Environment(loader=jinja2.FileSystemLoader(settings.template_dir))
    template=env.get_template(template_name)
    T=template.render(**context)
    T=T.encode('utf-8')
    return T

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

    def assertIsString(self,obj,msg=None):
        if not msg:
            msg="%s is not string (type: %s)" % (unicode(obj),type(obj))
        if type(obj) in [str,unicode]: return
        self.fail(msg)

    def assertIsList(self,obj,msg=None):
        if not msg:
            msg="%s is not string (type: %s)" % (unicode(obj),type(obj))
        if type(obj) in [list]: return
        self.fail(msg)

class StartResponseFactory(object):
    def __init__(self,cls,environ,status,response_headers):
        self.check_status=status
        self.check_response_headers=response_headers
        self.environ=environ
        self.cls=cls

    def __call__(self,status,response_headers):
            msg="%s: status received %s, expected %s" % (self.environ["PATH_INFO"],status,self.check_status)
            self.cls.assertEquals(status,self.check_status,msg=msg)
            for k,val in self.check_response_headers.items():
                self.cls.assertIn(k.lower(),map(lambda x: x.lower(),response_headers.keys()))
                self.cls.assertEquals(val.lower(),response_headers[k].lower())
            self.response_status=status
            self.response_headers=dict(map(lambda x: (x[0].lower(),x[1].lower()),response_headers))

    def check_length(self,response_body):
        size=len(response_body)
        k='content-length'
        self.cls.assertIn(k.lower(),self.response_headers.keys())
        self.cls.assertEquals(str(size),self.response_headers[k])

class GenerationTest(unittest.TestCase,AssertCollectionMixin):

    #config_example=BASE_DIR+"/config_test.json"
    base_dir=urltester.config.BASE_DIR
    template_dir=base_dir+u"/etc/templates"
    base_headers={
        'content-type':'text/html; charset=utf-8'
    }

    # default_paths=[ base_dir+u"/etc/urltester.conf" ]
    # default_title=u"UrlTester"
    # default_http_host=u"localhost"
    # default_http_port=9876
    # default_proxy_host=u""
    # default_proxy_port=3128
    # default_proxy_user=u""
    # default_proxy_password=u""

    def setUp(self):  
        pass

    def tearDown(self):  
        pass

    def test_functions(self):
        pass

    def _test_path(self,application,environ,status,headers):
        start_response=StartResponseFactory(self,environ,status,headers)
        response_body_list=application(environ,start_response)
        self.assertIsList(response_body_list)
        self.assertEquals(len(response_body_list),1)
        start_response.check_length(response_body_list[0])
        return response_body_list[0]

    def test_application(self):
        settings=urltester.config.Settings()
        server=urltester.server.UrlTester(settings)
        self.assertHasAttribute(server,"application")
        application=server.application
        def dummy_start_response(status,response_headers): pass
        environ={
            "SCRIPT_NAME": random_string(size=random.choice(range(0,1000))),
            "REQUEST_METHOD": random.choice(["get","post","put","delete","patch"]),
            "QUERY_STRING": random_string(size=random.choice(range(0,1000))),
            "CONTENT_TYPE": "text/html",
            "SERVER_PROTOCOL": "http"
        }

        for testurl in ["","config","environ"]+settings.url_defs.keys():
            if testurl=="":
                environ["PATH_INFO"]=""
            else:
                environ["PATH_INFO"]="/"+testurl

            response_body_1=self._test_path(application,environ,"200 OK",{})
            environ["PATH_INFO"]+="/"
            response_body_2=self._test_path(application,environ,"200 OK",{})

        for iteration in range(0,10):
            L=random.choice(range(1,50))
            testurl=random_string(L)
            while testurl in [ "environ","config" ]+settings.url_defs.keys(): testurl=random_string(L)
            environ["PATH_INFO"]="/"+testurl
            response_body_1=self._test_path(application,environ,"404 Not Found",{})
            environ["PATH_INFO"]+="/"
            response_body_2=self._test_path(application,environ,"404 Not Found",{})
            #self.assertEquals(response_body_1,response_body_2)

    def test_config(self):
        settings=urltester.config.Settings()
        server=urltester.server.UrlTester(settings)
        self.assertHasAttribute(server,"application")
        application=server.application
        def dummy_start_response(status,response_headers): pass
        environ={
            "SCRIPT_NAME": random_string(size=random.choice(range(0,1000))),
            "REQUEST_METHOD": random.choice(["get","post","put","delete","patch"]),
            "QUERY_STRING": random_string(size=random.choice(range(0,1000))),
            "CONTENT_TYPE": "text/html",
            "SERVER_PROTOCOL": "http"
        }

        testurl="config"

        environ["PATH_INFO"]="/"+testurl
        response_body_1=self._test_path(application,environ,"200 OK",{})
        environ["PATH_INFO"]+="/"
        response_body_2=self._test_path(application,environ,"200 OK",{})
        
        self.assertEquals(response_body_1,response_body_2)

        response_template=apply_template(settings,urltester.config.TEMPLATE_NAMES["config"],{})
        print response_template
        

if __name__ == '__main__':  
    unittest.main()
