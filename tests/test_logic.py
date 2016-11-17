#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
import os
import sys
import random
import string
import jinja2
import collections
import HTMLParser

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

CONFIG_FILE = PARENT_DIR+ "/etc/urltester.conf"

sys.path.append(PARENT_DIR+"/lib/python")

import urltester.config
import urltester.server
import urltester.tester

def apply_template(settings,template_name,context):
    env=jinja2.Environment(loader=jinja2.FileSystemLoader(settings.template_dir))
    template=env.get_template(template_name)
    T=template.render(**context)
    T=T.encode('utf-8')
    return T

def random_string(size=10, chars=string.ascii_lowercase +string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class AssertCollectionMixin(object):
    def _random_response(self):
        res=urltester.tester.TestResponse()
        if random.choice([True,False]):
            res.status=random.choice(range(100,699))
        else:
            res.status=-random.choice(range(1,30))
        res.time=float(random.choice(range(1,40)))
        res.msg="dummy test"
        res.errno=random.choice(range(0,100))
        return res

    def _random_response_collection(self,settings):
        coll=urltester.tester.TestResponseCollection(settings)
        for testurl in settings.url_defs.keys():
            resp=self._random_response()
            coll.add_response(testurl,resp)
        return coll

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
            msg="%s is not list (type: %s)" % (unicode(obj),type(obj))
        if type(obj) in [list]: return
        self.fail(msg)

    def assertIsDict(self,obj,msg=None):
        if not msg:
            msg="%s is not dict (type: %s)" % (unicode(obj),type(obj))
        if type(obj) in [dict]: return
        self.fail(msg)

    def assertStartsWith(self,S,start,msg=None):
        if not msg:
            msg="%s doesn't start with %s" % (S,start)
        if S.startswith(start): return
        self.fail(msg)

    def assertEndsWith(self,S,end,msg=None):
        if not msg:
            msg="%s doesn't end with %s" % (S,end)
        if S.endswith(end): return
        self.fail(msg)

    def get_server(self):
        settings=urltester.config.Settings()
        server=urltester.server.UrlTester(settings)
        return server,settings

    def get_environ(self):
        environ={
            "SCRIPT_NAME": "/"+random_string(size=random.choice(range(0,1000))),
            "REQUEST_METHOD": random.choice(["get","post","put","delete","patch"]),
            "QUERY_STRING": random_string(size=random.choice(range(0,1000))),
            "CONTENT_TYPE": "text/html",
            "SERVER_PROTOCOL": random.choice(["http","https"])
        }
        return environ
        

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
        self._check_is_page(server,"/docs",urltester.server.DocsPage)
        self._check_is_page(server,"/docs/",urltester.server.DocsPage)


        for testurl in settings.url_defs.keys():
            self._check_is_page(server,"/"+testurl,urltester.server.TestPage)
            self._check_is_page(server,"/"+testurl+"/",urltester.server.TestPage)

        for iteration in range(0,10):
            L=random.choice(range(1,50))
            testurl=random_string(L)
            while testurl in [ "environ","config","docs" ]+settings.url_defs.keys(): testurl=random_string(L)
            self._check_is_page(server,"/"+testurl,urltester.server.Error404Page)
            self._check_is_page(server,"/"+testurl+"/",urltester.server.Error404Page)

class GenerationTest(unittest.TestCase,AssertCollectionMixin):
    base_dir=urltester.config.BASE_DIR
    template_dir=base_dir+u"/etc/templates"
    base_headers={
        'content-type':'text/html; charset=utf-8'
    }

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
        context["static_url"]=context["base_url"]+"/"+urltester.config.STATIC_REL_PATH

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
        environ= self.get_environ()
        response_template=self._test_template_rendering(server,environ,"config","config",
                                                        { "title": settings.title+": configuration",
                                                          "settings": server.settings })

    def test_docs(self):
        server,settings=self.get_server()
        environ= self.get_environ()
        response_template=self._test_template_rendering(server,environ,"docs","docs",
                                                        { "title": settings.title+": documentation",
                                                          "settings": server.settings })

    def test_environ(self):
        server,settings=self.get_server()
        environ= self.get_environ()

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


    def _test_action_rendering(self,server,environ,testurl,template_id,context,equality_assert):
        self.assertHasAttribute(server,"application")
        application=server.application

        if testurl=="":
            environ["PATH_INFO"]=""
        else:
            environ["PATH_INFO"]="/"+testurl
        response_body_1=self._test_path(application,environ,"200 OK",{})

        environ["PATH_INFO"]+="/"
        response_body_2=self._test_path(application,environ,"200 OK",{})

        context["base_url"]=environ["SCRIPT_NAME"]
        context["static_url"]=context["base_url"]+"/"+urltester.config.STATIC_REL_PATH
        response_template=apply_template(server.settings,
                                         urltester.config.TEMPLATE_NAMES[template_id],
                                         context)

        equality_assert(response_body_1,response_body_2)
        equality_assert(response_body_1,response_template)

        return response_template


    def test_response_collection(self):
        server,settings=self.get_server()

        coll=urltester.tester.TestResponseCollection(settings)
        self.assertIsInstance(coll,collections.OrderedDict)
        test_data=collections.OrderedDict()
        for testurl in settings.url_defs.keys():
            resp=self._random_response()
            self.assertIn(testurl,coll.keys())
            self.assertIsDict(coll[testurl])
            self.assertIn("response",coll[testurl].keys())
            self.assertIn("definition",coll[testurl].keys())
            self.assertIn("ok",coll[testurl].keys())
            self.assertEquals(coll[testurl]["definition"],settings.url_defs[testurl])
            self.assertEquals(coll[testurl]["response"],None)
            coll.add_response(testurl,resp)
            self.assertEquals(coll[testurl]["response"],resp)
            self.assertEquals(coll[testurl]["ok"],settings.url_defs[testurl].check_status(resp.status))
            test_data[testurl]=resp


        ok_list=[]

        for testurl in settings.url_defs.keys():
            if test_data[testurl].status < 0:
                ok_list.append(False)
                continue
            ok_list.append( settings.url_defs[testurl].check_status(test_data[testurl].status) )

        all_ok=reduce(lambda x,y: x and y,ok_list,True)
        some_ok=reduce(lambda x,y: x or y,ok_list,False)

        if all_ok:
            test_ok=True
            msg=urltester.config.MESSAGES["all_ok"]
        elif some_ok:
            test_ok=True
            msg=urltester.config.MESSAGES["some_ok"]
        else:
            test_ok=False
            msg=urltester.config.MESSAGES["ko"]

        self.assertEquals(coll.msg,msg)
        self.assertEquals(coll.ok,test_ok)

    ### deve fare tutti i test
    def test_homepage(self):
        server,settings=self.get_server()
        environ= self.get_environ()

        action=random_string(size=random.choice(range(0,10)))
        environ["QUERY_STRING"]="action="+action

        def equality_assert(res1,res2):
            pass

        self._test_action_rendering(server,environ,"","homepage",
                                    { "title": settings.title,
                                      "settings": server.settings,
                                      "action": action,
                                      "test_time": 20,
                                      "res_collection": self._random_response_collection(settings) },
                                    equality_assert)

    def test_test(self):
        server,settings=self.get_server()
        environ= self.get_environ()

        action=random_string(size=random.choice(range(0,10)))
        environ["QUERY_STRING"]="action="+action

        def equality_assert(res1,res2):
            pass

        for testurl in settings.url_defs.keys():
            self._test_action_rendering(server,environ,testurl,"test",
                                        { "title": settings.title+": "+testurl,
                                          "settings": server.settings,
                                          "action": action,
                                          "test_name": testurl,
                                          "test_description": settings.url_defs[testurl],
                                          "test_response": self._random_response() }, equality_assert)

class Tag(dict):
    def __init__(self,parent,name,attrs):
        dict.__init__(self)
        self.parent=parent
        self.name=name
        self.attrs=attrs
        for k,val in self.attrs:
            self[k]=val
        self.children=[]
        self.data=[]

    def __str__(self):
        S=self.name
        if self.attrs:
            S+=" ["+",".join(map(lambda x: x[0]+'="'+x[1]+'"',self.attrs))+"]"
        return S

    def print_tree(self,prefix=""):
        S=self.name
        if self.attrs:
            S+=" ["+",".join(map(lambda x: x[0]+'="'+x[1]+'"',self.attrs))+"]"
        print "%s%s" % (prefix,S)

        txt=("".join(self.data)).strip()

        if txt:
            print "%s    %s" % (prefix,txt)
        if self.children:
            for ch in self.children:
                ch.print_tree(prefix=prefix+"    ")
            

class MyHTMLParser(HTMLParser.HTMLParser):
    def __init__(self,cls,static_url,title):
        HTMLParser.HTMLParser.__init__(self)
        self.static_url=static_url
        self.cls=cls
        self.status="out"
        self.title=title
        self.body_tree=None
        self._current_tag=None

    def handle_starttag(self, tag, attrs):
        self.current_tag=tag
        if tag in [ "head","body","html" ]:
            self.status=tag
            if tag!="body": return
            self.body_tree=Tag(None,tag,attrs)
            self._current_tag=self.body_tree
            return
        if tag=="link":
            for k,val in attrs:
                if k!="href": continue
                self.cls.assertStartsWith(val,self.static_url)
            return
        if self.status!="body": return

        new_tag=Tag(self._current_tag,tag,attrs)
        self._current_tag.children.append(new_tag)
        self._current_tag=new_tag

    def handle_endtag(self, tag):
        self.current_tag=None
        if tag in [ "head","body","html" ]:
            self.status="out"
            return
        if tag in [ "link","title" ]: 
            return
        if self.status!="body": return
        self._current_tag=self._current_tag.parent

    def handle_data(self, data):
        if self._current_tag=="title":
            self.cls.assertEquals(data,self.title)
            return
        if self.status!="body": return
        self._current_tag.data.append(data)

class RenderingTest(unittest.TestCase,AssertCollectionMixin):
    base_dir=urltester.config.BASE_DIR
    template_dir=base_dir+u"/etc/templates"
    base_headers={
        'content-type':'text/html; charset=utf-8'
    }

    def _template_rendering(self,server,template_id,context):
        context["base_url"]="/"+random_string(10)
        context["static_url"]=context["base_url"]+"/"+urltester.config.STATIC_REL_PATH
        response=apply_template(server.settings,
                                urltester.config.TEMPLATE_NAMES[template_id],
                                context)
        return response,context["static_url"]

    def test_config(self):
        server,settings=self.get_server()
        context={ "title": settings.title+": configuration",
                  "settings": server.settings }
        response,static_url=self._template_rendering(server,"config",context)

        # instantiate the parser and fed it some HTML
        parser = MyHTMLParser(self,static_url,context["title"])
        parser.feed(response)

        self.assertEqual(len(parser.body_tree.children),6)
        
        for k,val in [ (0,"header"),(2,"main"),(4,"footer") ]:
            self.assertEqual(parser.body_tree.children[k].name,"a")
            self.assertEqual(parser.body_tree.children[k]["name"],val)
            self.assertEqual(parser.body_tree.children[k+1].name,"div")
            self.assertEqual(parser.body_tree.children[k+1]["id"],val)

        for ch in parser.body_tree.children:
            print ch

        #parser.body_tree.print_tree()

        # L=filter(bool,map(lambda x: x.strip(),response.split("\n")))
        # print L
        # for row in L:
        #     print row

        
    def test_homepage(self):
        server,settings=self.get_server()

        context={ "title": settings.title,
                  "settings": server.settings,
                  "action": random_string(20),
                  "test_time": 20,
                  "res_collection": self._random_response_collection(settings) }


    def _test_test(self):
        server,settings=self.get_server()


        for testurl in settings.url_defs.keys():
            context={ 
                "title": settings.title+": "+testurl,
                "settings": server.settings,
                "action": action,
                "test_name": testurl,
                "test_description": settings.url_defs[testurl],
                "test_response": self._random_response() 
            }
            self._template_rendering(server,"test",context)



if __name__ == '__main__':  
    unittest.main()
