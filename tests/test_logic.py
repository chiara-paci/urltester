#!/usr/bin/python

import unittest
import os
import sys
import random
import string
import jinja2
import collections

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

    def get_server(self):
        settings=urltester.config.Settings()
        server=urltester.server.UrlTester(settings)
        return server,settings

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

class FunctionTest(unittest.TestCase,AssertCollectionMixin):
    def _check_is_page(self,server,path,page_class):
        page=server.path_map(path)
        self.assertIsInstance(page,page_class)

    def test_path_map(self):
        server,settings=self.get_server()
        self.assertHasAttribute(server,"path_map")
        self._check_is_page(server,"",urltester.server.HomePage)
        self._check_is_page(server,"/",urltester.server.HomePage)
        self._check_is_page(server,"/config",urltester.server.ConfigPage)
        self._check_is_page(server,"/config/",urltester.server.ConfigPage)
        self._check_is_page(server,"/environ",urltester.server.EnvironPage)
        self._check_is_page(server,"/environ/",urltester.server.EnvironPage)


        for testurl in settings.url_defs.keys():
            self._check_is_page(server,"/"+testurl,urltester.server.TestPage)
            self._check_is_page(server,"/"+testurl+"/",urltester.server.TestPage)

        for iteration in range(0,10):
            L=random.choice(range(1,50))
            testurl=random_string(L)
            while testurl in [ "environ","config" ]+settings.url_defs.keys(): testurl=random_string(L)
            self._check_is_page(server,"/"+testurl,urltester.server.Error404Page)
            self._check_is_page(server,"/"+testurl+"/",urltester.server.Error404Page)

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

    def _test_path(self,application,environ,status,headers):
        start_response=StartResponseFactory(self,environ,status,headers)
        response_body_list=application(environ,start_response)
        self.assertIsList(response_body_list)
        self.assertEquals(len(response_body_list),1)
        start_response.check_length(response_body_list[0])
        return response_body_list[0]

    def test_application(self):
        server,settings=self.get_server()
        self.assertHasAttribute(server,"application")
        application=server.application
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

    def _test_template_rendering(self,server,environ,testurl,template_id,context):
        self.assertHasAttribute(server,"application")
        application=server.application

        if testurl=="":
            environ["PATH_INFO"]=""
        else:
            environ["PATH_INFO"]="/"+testurl
        response_body_1=self._test_path(application,environ,"200 OK",{})
        environ["PATH_INFO"]+="/"
        response_body_2=self._test_path(application,environ,"200 OK",{})
        
        self.assertEquals(response_body_1,response_body_2)

        context["base_url"]=environ["SCRIPT_NAME"]

        response_template=apply_template(server.settings,
                                         urltester.config.TEMPLATE_NAMES[template_id],
                                         context)

        template_rows=response_template.split('\n')
        body_rows=response_body_1.split('\n')
        self.assertEquals(len(template_rows),len(body_rows))
        L=len(template_rows)
        for n in range(0,L):
            self.assertEquals(template_rows[n],body_rows[n])
        return response_template

    def test_config(self):
        server,settings=self.get_server()

        environ={
            "SCRIPT_NAME": random_string(size=random.choice(range(0,1000))),
            "REQUEST_METHOD": random.choice(["get","post","put","delete","patch"]),
            "QUERY_STRING": random_string(size=random.choice(range(0,1000))),
            "CONTENT_TYPE": "text/html",
            "SERVER_PROTOCOL": "http"
        }

        response_template=self._test_template_rendering(server,environ,"config","config",
                                                        { "title": settings.title+": configuration",
                                                          "settings": server.settings })
        print response_template
        print settings.url_defs

    def test_environ(self):
        server,settings=self.get_server()
        environ={
            "SCRIPT_NAME": random_string(size=random.choice(range(0,1000))),
            "REQUEST_METHOD": random.choice(["get","post","put","delete","patch"]),
            "QUERY_STRING": random_string(size=random.choice(range(0,1000))),
            "CONTENT_TYPE": "text/html",
            "SERVER_PROTOCOL": "http"
        }

        local_environ=collections.OrderedDict()
        keys=environ.keys()+["PATH_INFO"]
        keys.sort()
        for k in keys:
            if k=="PATH_INFO":
                local_environ[k]="/environ/"
                continue
            local_environ[k]=environ[k]
            
        self._test_template_rendering(server,environ, "environ","environ",
                                      { "title": settings.title+": environment",
                                        "environ": local_environ })
        

    ### deve fare tutti i test
    def test_homepage(self):
        server,settings=self.get_server()

        action="notest"

        environ={
            "SCRIPT_NAME": random_string(size=random.choice(range(0,1000))),
            "REQUEST_METHOD": random.choice(["get","post","put","delete","patch"]),
            "QUERY_STRING": "action="+action,
            "CONTENT_TYPE": "text/html",
            "SERVER_PROTOCOL": "http"
        }

        self._test_template_rendering(server,environ,"","homepage",
                                      { "title": settings.title,
                                        "settings": server.settings,
                                        "action": action })

    def test_test(self):
        server,settings=self.get_server()

        action=random_string(size=random.choice(range(0,10)))
        environ={
            "SCRIPT_NAME": random_string(size=random.choice(range(0,1000))),
            "REQUEST_METHOD": random.choice(["get","post","put","delete","patch"]),
            "QUERY_STRING": "action="+action,
            "CONTENT_TYPE": "text/html",
            "SERVER_PROTOCOL": "http"
        }

        for testurl in settings.url_defs.keys():
            self._test_template_rendering(server,environ,testurl,"test",
                                          { "title": settings.title+": "+testurl,
                                            "settings": server.settings,
                                            "action": action,
                                            "test_name": testurl,
                                            "test_description": settings.url_defs[testurl] })
        

if __name__ == '__main__':  
    unittest.main()
