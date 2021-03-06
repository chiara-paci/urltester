#!/usr/bin/env python

import os
import unittest
import json
import sys
import collections
import random

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

CONFIG_FILE = PARENT_DIR+ "/etc/urltester.conf"

sys.path.append(PARENT_DIR+"/lib/python")

import urltester.config

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

    def assertIsBoolean(self,obj,msg=None):
        if not msg:
            msg="%s is not boolean (type: %s)" % (unicode(obj),type(obj))
        if type(obj) in [bool]: return
        self.fail(msg)

    def assertIsList(self,obj,msg=None):
        if not msg:
            msg="%s is not list (type: %s)" % (unicode(obj),type(obj))
        if type(obj) in [list]: return
        self.fail(msg)

class ConfigTest(unittest.TestCase,AssertCollectionMixin):
    config_example=BASE_DIR+"/config_test.json"
    base_dir=urltester.config.BASE_DIR
    default_paths=[ base_dir+u"/etc/urltester.conf" ]
    default_title=u"UrlTester"
    default_http_host=u"localhost"
    default_http_port=9876
    default_proxy_host=u""
    default_proxy_port=3128
    default_proxy_user=u""
    default_proxy_password=u""
    default_template_dir=base_dir+u"/etc/templates"
    default_base_context=u""
    default_serve_static=False
    default_static_dir=base_dir+u"/static"

    def setUp(self):  
        pass

    def tearDown(self):  
        pass

    def _test_settings_base(self,settings,http_host,http_port,paths,title,template_dir,
                            proxy_host,proxy_port,proxy_user,proxy_password,base_context,
                            serve_static,static_dir):

        self.assertEqual(title,unicode(settings))

        self.assertHasAttribute(settings,"paths")
        self.assertEqual(settings.paths,paths)

        self.assertHasAttribute(settings,"version")
        self.assertEqual(settings.version,urltester.config.VERSION)

        self.assertHasAttribute(settings,"http_host")
        self.assertIsString(settings.http_host)
        self.assertEqual(settings.http_host,http_host)

        self.assertHasAttribute(settings,"http_port")
        self.assertIsInteger(settings.http_port)
        self.assertEqual(settings.http_port,http_port)

        self.assertHasAttribute(settings,"proxy_host")
        self.assertIsString(settings.proxy_host)
        self.assertEqual(settings.proxy_host,proxy_host)

        self.assertHasAttribute(settings,"proxy_port")
        self.assertIsInteger(settings.proxy_port)
        self.assertEqual(settings.proxy_port,proxy_port)

        self.assertHasAttribute(settings,"proxy_user")
        self.assertIsString(settings.proxy_user)
        self.assertEqual(settings.proxy_user,proxy_user)

        self.assertHasAttribute(settings,"proxy_password")
        self.assertIsString(settings.proxy_password)
        self.assertEqual(settings.proxy_password,proxy_password)

        self.assertHasAttribute(settings,"template_dir")
        self.assertIsString(settings.template_dir)
        self.assertEqual(settings.template_dir,template_dir)

        self.assertHasAttribute(settings,"static_dir")
        self.assertIsString(settings.static_dir)
        self.assertEqual(settings.static_dir,static_dir)

        self.assertHasAttribute(settings,"title")
        self.assertIsString(settings.title)
        self.assertEqual(settings.title,title)

        self.assertHasAttribute(settings,"url_defs")
        self.assertIsInstance(settings.url_defs,collections.OrderedDict)

        self.assertHasAttribute(settings,"base_context")
        self.assertIsString(settings.base_context)
        self.assertEqual(settings.base_context,base_context)

        self.assertHasAttribute(settings,"serve_static")
        self.assertIsBoolean(settings.serve_static)
        self.assertEqual(settings.serve_static,serve_static)

    

    def test_load_settings(self):
        
        def get_args(args,k="",val=""):
            ret=args.copy()
            if k:
                ret[k]=val
            return ret.values()

        settings=urltester.config.Settings()

        base_args=collections.OrderedDict([
            ("http_host",self.default_http_host),
            ("http_port",self.default_http_port),
            ("paths",self.default_paths),
            ("title",self.default_title),
            ("template_dir",self.default_template_dir),
            ("proxy_host",self.default_proxy_host),
            ("proxy_port",self.default_proxy_port),
            ("proxy_user",self.default_proxy_user),
            ("proxy_password",self.default_proxy_password),
            ("base_context",self.default_base_context),
            ("serve_static",self.default_serve_static),
            ("static_dir", self.default_static_dir)
        ])
        
        args=get_args(base_args)
        self._test_settings_base(settings,*args)

        with self.assertRaises(urltester.config.SettingsException):
            urltester.config.Settings(paths={ u"ciao": "ciao" })

        with self.assertRaises(urltester.config.SettingsException):
            urltester.config.Settings(http_port=u"ciao")

        with self.assertRaises(urltester.config.SettingsException):
            urltester.config.Settings(proxy_port=u"ciao")

        with self.assertRaises(urltester.config.SettingsException):
            urltester.config.Settings(template_dir=[ u"ciao" ])

        with self.assertRaises(urltester.config.SettingsException):
            urltester.config.Settings(static_dir=[ u"ciao" ])

        for k,val in [ 
                ("http_host",u""),
                ("http_port",12345),
                ("title",u"Nuovo titolo"),
                ("paths",[ "/ciao" ]),
                ("template_dir",u"/ciao"),
                ("static_dir",u"/ciao"),
                ("proxy_host",u"ciao"),
                ("proxy_port",12345),
                ("proxy_user",u"pippo"),
                ("proxy_password",u"ciao"),
                ("base_context",u"/ciao/uyte"),
                ("serve_static",True),
        ]:
            kwargs={ k:val }
            settings=urltester.config.Settings(**kwargs)
            args=get_args(base_args,k,val)
            self._test_settings_base(settings,*args)

    def test_config_reading(self):
        test_data=[]
        for path in self.default_paths:
            if not (os.path.isfile(path) and os.access(path, os.R_OK)):
                continue
            fd=open(path,"r")
            data=json.load(fd)
            fd.close()
            test_data+=data

        settings=urltester.config.Settings()

        self._check_configuration(settings,self.default_paths,test_data)
        
    def test_config_parsing(self):
        test_data=[
            {
                u"context": u"context1",
                u"url": u"http://sito.prova.it/pinco/pallo?ghye&3",
                u"title": u"Titolo di context1",
                u"affects": u"Turismo, SIU, Collaudi regionali, IAM, etc",
                u"status_ok": u"any",
                u"timeout": 30
            },
            {
                u"context": u"abc345",
                u"url": u"http://sito.prova.it/pinco",
                u"title": u"Titolo di abc 345",
                u"affects": u"Turismo, SI",
                u"status_ok": [ u"200", u"404" ],
                u"timeout": 45
            },
            {
                u"context": u"qef",
                u"url": u"http://sito.prova.it/pinco/pallo%20gsh",
                u"title": u"Qef",
                u"affects": u"Collaudi regionali, IAM, etc",
                u"status_ok": [ u"200:399", u"404" ],
                u"timeout": 60,
                u"ssl_client_key": "pippo",
                u"ssl_client_cert": "pippo",
            },
            {
                u"context": u"qefghq",
                u"url": u"http://sito.prova2.it/pinco/pallo%20gsh",
                u"title": u"Qef Ghq",
                u"affects": u"Collaudi regionali, IAM, etc",
                u"status_ok": [ u"200:399", u"404", 500 ],
                u"timeout": 60,
                u"no_ssl_v2": True,
            },
            
        ]

        fd=open(self.config_example,"w")
        json.dump(test_data,fd,indent=4)
        fd.close()
        
        settings=urltester.config.Settings(paths=self.config_example)
        self._check_configuration(settings,[self.config_example],test_data)

    def test_config_other(self):
        test_data=[]
        paths=[PARENT_DIR+"/tests/real_test.conf"]
        for path in paths:
            if not (os.path.isfile(path) and os.access(path, os.R_OK)):
                continue
            fd=open(path,"r")
            data=json.load(fd)
            fd.close()
            test_data+=data

        settings=urltester.config.Settings(paths=paths)

        self._check_configuration(settings,paths,test_data)

    def _check_configuration(self,settings,paths,test_data):
        keys=[]
        keys=map(lambda x: x[u"context"],test_data)

        self._test_settings_base(settings,self.default_http_host,self.default_http_port,
                                 paths,self.default_title,self.default_template_dir,
                                 self.default_proxy_host,self.default_proxy_port,
                                 self.default_proxy_user,self.default_proxy_password,
                                 self.default_base_context,
                                 self.default_serve_static,self.default_static_dir)
        
        self.assertEquals(keys,settings.url_defs.keys())

        for tdict in test_data:
            k=tdict[u"context"]
            self.assertIsInstance(settings.url_defs[k],urltester.config.TestDescription)
            self.assertHasAttribute(settings.url_defs[k],"check_status")
            self.assertIsInstance(settings.url_defs[k].check_status,urltester.config.CheckStatus)
            self.assertEquals(tdict[u"status_ok"],settings.url_defs[k].check_status.status_ok_defs)
            self.assertEquals(tdict[u"context"],settings.url_defs[k].context)
            self.assertEquals(tdict[u"url"],settings.url_defs[k].url)
            self.assertEquals(tdict[u"title"],settings.url_defs[k].title)
            self.assertEquals(tdict[u"affects"],settings.url_defs[k].affects)
            self.assertEquals(tdict[u"timeout"],settings.url_defs[k].timeout)
            for attr in [ u"no_ssl_v2",u"no_ssl_v3",u"ssl_check_certificate",
                          u"ssl_client_key",u"ssl_client_cert",u"ssl_cipher"]:
                self.assertHasAttribute(settings.url_defs[k],attr)
                val=settings.url_defs[k].__getattribute__(attr)
                if attr in tdict.keys():
                    self.assertEquals(tdict[attr],val)
                    continue
                if attr=="ssl_check_certificate":
                    self.assertEquals(True,val)
                elif attr in [ u"ssl_client_key",u"ssl_client_cert",u"ssl_cipher" ]:
                    self.assertEquals("",val)
                else:
                    self.assertEquals(False,val)
                    

    def test_check_status(self):
        # valori validi e significato per status_ok:
        # (a) "any": sempre ok
        # (b) int o coercible: singolo stato
        # (c) stringa "int:int" oppure "int:int:int": range
        # (d) lista di (b) o (c)

        with self.assertRaises(urltester.config.ConfigException):
            urltester.config.CheckStatus({ u"ciao": "ciao" })
        with self.assertRaises(urltester.config.ConfigException):
            urltester.config.CheckStatus("ciao")
        with self.assertRaises(urltester.config.ConfigException):
            urltester.config.CheckStatus("")
        with self.assertRaises(urltester.config.ConfigException):
            urltester.config.CheckStatus(":34")
        with self.assertRaises(urltester.config.ConfigException):
            urltester.config.CheckStatus("12:34:23:3")
        with self.assertRaises(urltester.config.ConfigException):
            urltester.config.CheckStatus(["ciao",3])
        with self.assertRaises(urltester.config.ConfigException):
            urltester.config.CheckStatus(3.4)

        def assert_true(check,status,req):
            msg="False for %d on request: %s" % (status,req)
            self.assertTrue(check(n),msg=msg)

        def assert_false(check,status,req):
            msg="True for %d on request: %s" % (status,req)
            self.assertFalse(check(n),msg=msg)


        def random_test_scalar(test_type):
            if test_type in ["int","str","unicode"]:
                val=random.choice(range(100,600))
                if test_type=="int": return val, [val]
                if test_type=="str": return str(val), [val]
                return unicode(val), [val]
            val_1=random.choice(range(100,600))
            val_2=random.choice(range(100,600))
            while val_1==val_2: val_2=random.choice(range(100,600))
            val_min=min(val_1,val_2)
            val_max=max(val_1,val_2)
            if test_type in ["range","urange"]:
                if test_type=="range":
                    return str(val_min)+":"+str(val_max) , range(val_min,val_max+1)
                return unicode(val_min)+u":"+unicode(val_max) , range(val_min,val_max+1)
            step=random.choice(range(1,100))
            if test_type=="range":
                return str(val_min)+":"+str(step)+":"+str(val_max) , range(val_min,val_max+1,step)
            return unicode(val_min)+u":"+unicode(step)+u":"+unicode(val_max) , range(val_min,val_max+1,step)

        req="any"
        check_status=urltester.config.CheckStatus(req)
        for n in range(100,599):
            assert_true(check_status,n,req)

        for test_type in ["int","str","unicode","range","steprange","urange","usteprange"]:
            req,test_list=random_test_scalar(test_type)
            check_status=urltester.config.CheckStatus(req)
            for n in range(100,599):
                if n in test_list:
                    assert_true(check_status,n,req)
                    continue
                assert_false(check_status,n,req)

        for iteration in range(0,3):
            L=random.choice(range(1,10))
            req=[]
            test_list=[]
            for l in range(0,L):
                test_type=random.choice(["int","str","unicode","range","steprange","urange","usteprange"])
                s_req,s_list=random_test_scalar(test_type)
                req.append(s_req)
                test_list+=s_list

            check_status=urltester.config.CheckStatus(req)
            for n in range(100,599):
                if n in test_list:
                    assert_true(check_status,n,req)
                    continue
                assert_false(check_status,n,req)


if __name__ == '__main__':  
    unittest.main()
