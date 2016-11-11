import collections
import json
import os
import re

## config section

BASE_DIR=u"/home/chiara/urltester"
VERSION_FILE=BASE_DIR+"/VERSION"

## stop editing
fd=open(VERSION_FILE)
VERSION=fd.read().strip()
fd.close()

def to_unicode(S):
    if type(S)==unicode: return S
    return unicode(S)

class SettingsException(Exception):
    def __init__(self,attribute,expected_type,value):
        self.attribute=attribute
        self.expected_type=expected_type
        self.value=value

    def __str__(self):
        msg="attribute %s is not of type %s (it's %s)" % (self.attribute,self.expected_type,type(self.value))
        return msg

class ConfigException(Exception):
    def __init__(self,attribute,expected_type,value,reason):
        self.attribute=attribute
        self.expected_type=expected_type
        self.value=value
        self.reason=reason

    def __str__(self):
        if self.reason=="invalid type":
            msg="attribute %s: is not of type %s (it's %s)" % (self.attribute,self.expected_type,type(self.value))
            return msg
        msg="attribute %s: invalid value %s (%s)" % (self.attribute,self.value,self.reason)
        return msg

class CheckStatus(object):
    re_ok_int=re.compile(r'[0-9]+')
    re_ok_range=re.compile(r'^[0-9]+(:[0-9]+){0,2}$')

    def __init__(self,status_ok_defs):
        self.status_ok_defs=self._is_ok(status_ok_defs)
    
    def _is_ok(self,status_ok_defs):
        if type(status_ok_defs)==int: return status_ok_defs
        if type(status_ok_defs) not in [ str,unicode,list,tuple ]:
            raise ConfigException("status_ok","int,str,unicode,list or tuple",status_ok_defs,"invalid type")
        if type(status_ok_defs) in [ str,unicode ]:
            if status_ok_defs==u"any": return  status_ok_defs
            if self.re_ok_range.match(status_ok_defs): return  status_ok_defs
            raise ConfigException("status_ok","int,str,unicode,list or tuple",status_ok_defs,"invalid value A")
        for req in status_ok_defs:
            if type(req)==int: continue
            if self.re_ok_range.match(req): continue
            raise ConfigException("status_ok","int,str,unicode,list or tuple",status_ok_defs,"invalid value ("+str(req)+")")
        return status_ok_defs

    def _check_status_scalar(self,status,status_cfr):
        if type(status_cfr) in [int]:
            return (status_cfr==status)
        if type(status_cfr) not in [unicode,str]:
            return False
        if status_cfr.isdigit():
            return(int(status_cfr)==status)

        t=status_cfr.split(":")

        if len(t) not in [2,3]: return False

        if t[0]=="":
            status_min=0
        elif t[0].isdigit():
            status_min=int(t[0])
        else:
            return False

        if t[-1]=="":
            status_max=0
        elif t[-1].isdigit():
            status_max=int(t[-1])
        else:
            return False

        if len(t)==2:
            step=1
        elif t[1]=="": 
            step=1
        elif t[1].isdigit():
            step=int(t[1])
        else:
            return False

        return status in range(status_min,status_max+1,step)

    def __call__(self,status):
        if self.status_ok_defs == u"any":
            return True
        if type(self.status_ok_defs) in [str,unicode,int]:
            return self._check_status_scalar(status,self.status_ok_defs)
        for status_cfr in self.status_ok_defs:
            if self._check_status_scalar(status,status_cfr):
                return True
        return False

class TestDescription(object):
    def __init__(self,tdict):
        self.context=tdict[u"context"]
        self.url=tdict[u"url"]
        self.title=tdict[u"title"]
        self.affects=tdict[u"affects"]
        self.timeout=tdict[u"timeout"]
        self.check_status=CheckStatus(tdict[u"status_ok"])

class Settings(object):
    def __init__(self,http_host=u"localhost",http_port=9876,
                 paths=[ BASE_DIR+u"/etc/urltester.conf" ],title=u"UrlTester Settings",
                 template_dir=BASE_DIR+u"/var/templates",
                 proxy_host=u"",proxy_port=3128,proxy_user=u"",proxy_password=u""): 
        if type(paths) in [list,tuple]:
            self.paths=paths
        elif type(paths) in [unicode,str,int]:
            self.paths=[ to_unicode(paths) ]
        else:
            raise SettingsException("paths","list/unicode",paths)

        self.title=to_unicode(title)
        self.http_host=to_unicode(http_host)
        self.proxy_host=to_unicode(proxy_host)
        self.proxy_user=to_unicode(proxy_user)
        self.proxy_password=to_unicode(proxy_password)

        try:
            self.http_port=int(http_port)
        except ValueError, e:
            raise SettingsException("http_port","int",http_port)

        try:
            self.proxy_port=int(proxy_port)
        except ValueError, e:
            raise SettingsException("proxy_port","int",proxy_port)

        if type(template_dir) not in [str,unicode,int]:
            raise SettingsException("template_dir","unicode",template_dir)
            
        self.template_dir=to_unicode(template_dir)
        self.url_defs=collections.OrderedDict()

        self.load()

    def load(self):
        for path in self.paths:
            if not (os.path.isfile(path) and os.access(path, os.R_OK)):
                continue
            fd=open(path,"r")
            data=json.load(fd)
            fd.close()

            for desc in data:
                self.url_defs[desc[u"context"]]=TestDescription(desc)

    def __unicode__(self): 
        return self.title
