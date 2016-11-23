# -*- coding: utf-8 -*-

import time
import urllib2
import httplib
import socket
import ssl
import collections
import threading

import config

class TestResponse(object):
    ssl_bad_list = ["CERTIFICATE_VERIFY_FAILED",
                    "SSLV3_ALERT_HANDSHAKE_FAILURE"]
    def __init__(self):
        self.status=200
        self.time=0.0
        self.msg=""
        self.errno=0

    def _ssl_status(self,exception,parent):
        if not hasattr(exception,"reason"):
            if parent:
                return -10
            return -11
        if exception.reason in self.ssl_bad_list:
            if parent:
                return -12
            return -13
        if parent:
            return 601
        return 600

    def add_error(self,exception,parent=None):
        if isinstance(exception,urllib2.URLError):
            if type(exception.reason) in [str,unicode]:
                self.status=-1
                self.msg=config.to_unicode(exception.reason)
                return
            return self.add_error(exception.reason,parent=exception)
        if isinstance(exception,ssl.SSLError):
            if type(exception.errno)==int:
                self.errno=exception.errno
            self.msg="SSL Error (unknown)"
            if exception.strerror:
                self.msg="SSL Error: %s" % (exception.strerror)
            elif exception.message:
                self.msg="SSL Error: %s" % (exception.message)
                
            self.status=self._ssl_status(exception,parent)
            if parent:
                self.msg+=" "+unicode(type(parent))
            return
        if isinstance(exception,socket.timeout):
            self.status=-2
            self.msg="Timed out"
            return
        if isinstance(exception,socket.gaierror) or isinstance(exception,socket.herror):
            self.status=-3
            self.msg="Address related error: %s" % (exception.args[1])
            self.errno=exception.args[0]
            return
        if isinstance(exception,socket.error):
            if type(exception.errno)==int:
                self.errno=exception.errno
            elif len(exception.args)==2:
                self.errno=exception.args[0]
            self.msg="Socket Error (unknown)"
            if exception.strerror:
                self.msg="Socket Error: %s" % (exception.strerror)
            elif exception.message:
                self.msg="Socket Error: %s" % (exception.message)
            elif len(exception.args)==2:
                self.msg="Socket Error: %s" % (exception.args[1])
            if parent:
                self.status=-6
                self.msg+=" "+unicode(type(parent))
            else:
                self.status=-7
            return
        self.status=-100
        self.msg="(%s) %s" % (unicode(type(exception)),unicode(exception))
        if hasattr(exception,"errno") and type(exception.errno)==int: 
            self.errno=errno

class TestResponseCollection(collections.OrderedDict):
    def __init__(self,settings):
        collections.OrderedDict.__init__(self)
        self.settings=settings
        for testname,test_def in self.settings.url_defs.items():
            self[testname]={
                "response": None,
                "definition": test_def,
                "ok": False
            }
        self._ok_dict={}

    @property
    def msg(self):
        all_ok=reduce(lambda x,y: x and y,self._ok_dict.values(),True)
        some_ok=reduce(lambda x,y: x or y,self._ok_dict.values(),False)
        if all_ok:
            return config.MESSAGES["all_ok"]
        if some_ok:
            return config.MESSAGES["some_ok"]
        return config.MESSAGES["ko"]

    @property
    def ok(self):
        all_ok=reduce(lambda x,y: x and y,self._ok_dict.values(),True)
        some_ok=reduce(lambda x,y: x or y,self._ok_dict.values(),False)
        return all_ok or some_ok

    @property
    def all_ok(self):
        all_ok=reduce(lambda x,y: x and y,self._ok_dict.values(),True)
        return all_ok

    @property
    def some_ok(self):
        some_ok=reduce(lambda x,y: x or y,self._ok_dict.values(),False)
        return some_ok

    def add_response(self,testname,response):
        self[testname]["response"]=response
        self[testname]["ok"]=self[testname]["definition"].check_status(response.status)
        self._ok_dict[testname]=self[testname]["ok"]

class Tester(object):
    def __init__(self,settings,test_name):
        self.settings=settings
        self.test_name=test_name

        self.url=settings.url_defs[test_name].url
        self.timeout=settings.url_defs[test_name].timeout
        self.ssl_check_certificate=settings.url_defs[test_name].ssl_check_certificate
        self.no_ssl_v2=settings.url_defs[test_name].no_ssl_v2
        self.no_ssl_v3=settings.url_defs[test_name].no_ssl_v3
        self.ssl_client_key=settings.url_defs[test_name].ssl_client_key
        self.ssl_client_cert=settings.url_defs[test_name].ssl_client_cert
        self.ssl_cipher=settings.url_defs[test_name].ssl_cipher

    def execute(self):
        response=TestResponse()

        gcontext=ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        if self.ssl_check_certificate:
            gcontext.verify_mode=ssl.CERT_REQUIRED
            gcontext.load_default_certs()
            gcontext.check_hostname=True
        else:
            gcontext.verify_mode=ssl.CERT_NONE
        if self.no_ssl_v2:
            gcontext.options |= ssl.OP_NO_SSLv2
        if self.no_ssl_v3:
            gcontext.options |= ssl.OP_NO_SSLv3
        if self.ssl_client_cert:
            if self.ssl_client_key:
                gcontext.load_cert_chain(self.ssl_client_cert,keyfile=self.ssl_client_key)
            else:
                gcontext.load_cert_chain(self.ssl_client_cert)
        if self.ssl_cipher:
            gcontext.set_ciphers(self.ssl_cipher)

        handlers=[urllib2.HTTPSHandler(context=gcontext)]
        if self.settings.proxy_host:
            proxy=self.settings.proxy_host+":"+unicode(self.settings.proxy_port)
            proxy_handler = urllib2.ProxyHandler({'http': proxy,'https': proxy})
            handlers.append(proxy_handler)
        opener=urllib2.build_opener(*handlers)

        t0=time.time()

        try:
            f=opener.open(self.url,timeout=self.timeout)
            data=f.read()
            response.status=f.code
            f.close()
        except urllib2.HTTPError, e:
            response.status=e.code
            response.msg=config.to_unicode(e.reason)
        except Exception, e:
            response.add_error(e)

        t1=time.time()

        response.time=t1-t0

        return response

def tester_factory(settings,testname):
    tester=Tester(settings,testname)
    return tester

class TestManager(object):
    def __init__(self,settings):
        self.settings=settings

    def run_sequential(self):
        t0=time.time()
        ret=TestResponseCollection(self.settings)
        for testname in self.settings.url_defs.keys():
            tester=tester_factory(self.settings,testname)
            test_response=tester.execute()
            ret.add_response(testname,test_response)
        t1=time.time()
        return t1-t0,ret

    def run_threaded(self):
        t0=time.time()
        ret=TestResponseCollection(self.settings)
        thread_dict={}
        for testname in self.settings.url_defs.keys():
            tester=tester_factory(self.settings,testname)
            thread_dict[testname]=TestThread(tester)
            thread_dict[testname].start()
        terminated=False
        while not terminated:
            terminated=True
            for th in thread_dict.values():
                terminated = terminated and (not th.is_alive())

        for testname in self.settings.url_defs.keys():
            ret.add_response(testname,thread_dict[testname].response)
        
        t1=time.time()
        return t1-t0,ret

class TestThread(threading.Thread):
    def __init__(self,tester):
        threading.Thread.__init__(self)
        self.tester=tester
        self.response=None

    def run(self):
        self.response=self.tester.execute()
