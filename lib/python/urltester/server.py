# -*- coding: utf-8 -*-

# Python's bundled WSGI server
import wsgiref.simple_server
import random
import jinja2
import collections
import inspect
import mimetypes

import logging

import config
import tester

class Response(object):
    def __init__(self,content_type='text/html; charset=utf-8'):
        self.body=u""
        self.headers = [
            ('Content-Type', content_type),
            ('Content-Length', str(len(self.body)))
        ]
        self.status="200 OK"

    @property
    def body_iterable(self):
        return [self.body]

    def finalize_headers(self):
        new_headers=[]
        for k,val in self.headers:
            if k!="Content-Length":
                new_headers.append( (k,val) )
            new_headers.append( ('Content-Length', str(len(self.body))) )
        self.headers=new_headers

class StaticResponse(object):
    def __init__(self,file_path):
        self.file_path=file_path
        mimetypes.add_type('application/x-font-woff2',".woff2")
        mimetypes.add_type('application/x-font-opentype',".otf")
        mimetypes.add_type('application/x-font-truetype',".ttf")

        c_type,c_enc=mimetypes.guess_type(self.file_path)
        self.headers = [
            ('Content-Type', c_type),
        ]
        self.status="200 OK"

    @property
    def body_iterable(self):
        fd=open(self.file_path,"r")
        return wsgiref.util.FileWrapper(fd)

class StaticPage(object):
    def __init__(self,obj_path,settings):
        self.obj_path=obj_path
        self.settings=settings

    def get(self,environ):
        file_path=self.settings.static_dir+self.obj_path
        response=StaticResponse(file_path)
        return response

class TemplatePage(object):
    template_name=config.TEMPLATE_NAMES["test"]
    page_title=""
    
    def __init__(self,settings): 
        self.settings=settings

    def get_title(self):
        if not self.page_title:
            return self.settings.title
        return self.settings.title+": "+self.page_title

    def elab(self,context,environ): 
        return "200 OK",context

    def get(self,environ):
        response=Response()
        prefix=environ["SCRIPT_NAME"]+self.settings.base_context

        context={
            "title": self.get_title(),
            "base_url": prefix,
            "static_url": prefix+"/"+config.STATIC_REL_PATH
        }
        status,context=self.elab(context,environ)
        response.body = self.apply_template(self.template_name,context)
        response.status=status
        response.finalize_headers()
        return response
        
    def apply_template(self,template_name,context):
        env=jinja2.Environment(loader=jinja2.FileSystemLoader(self.settings.template_dir))
        template=env.get_template(template_name)
        T=template.render(**context)
        T=T.encode('utf-8')
        return T
    
class ConfigPage(TemplatePage):
    template_name=config.TEMPLATE_NAMES["config"]
    page_title="configuration"

    def elab(self,context,environ):
        context["settings"]=self.settings
        return "200 OK",context

class DocsPage(TemplatePage):
    template_name=config.TEMPLATE_NAMES["docs"]
    page_title="documentation"

    def elab(self,context,environ):
        context["settings"]=self.settings

        context["params_settings"]=collections.OrderedDict()
        args,varargs,keywords,defaults=inspect.getargspec(self.settings.__init__)
        delta=len(args)-len(defaults)
        for n in range(1,len(args)):
            context["params_settings"][args[n]]={ "default": None,"doc": u"","type": None }
            if hasattr(self.settings,args[n]):
                attr=getattr(self.settings,args[n])
                if type(attr)==int:
                    context["params_settings"][args[n]]["type"]="int"
                elif type(attr)==float:
                    context["params_settings"][args[n]]["type"]="float"
                elif type(attr)==list:
                    context["params_settings"][args[n]]["type"]="string/list"
                else:
                    context["params_settings"][args[n]]["type"]="string"
            if n<delta: continue
            context["params_settings"][args[n]]["default"]=defaults[n-delta]

        context["params_tests"]=collections.OrderedDict( [
            ( "context", {"type": "str","mandatory": True,
                          "description": "context della pagina del test"} ),
            ( "url", {"type": "str","mandatory": True,
                      "description": "url da testare"} ),
            ( "title", {"type": "str","mandatory": True,
                        "description": "nome descrittivo del test"} ),
            ( "affects", {"type": "str","mandatory": True,
                          "description": "elenco dei sistemi impattati"} ),
            ( "timeout", {"type": "float","mandatory": True,
                          "description": "timeout per l'apertura dell'url"} ),
            ( "status_ok", {"type": "int/str/list","mandatory": True,
                            "description": "status http che sono considerati validi (v. sotto)"} ),
            ( "no_ssl_v2", {"type": "bool","mandatory": False,"default": "false",
                            "description": "escludere l'SSLv2"} ),
            ( "no_ssl_v3", {"type": "bool","mandatory": False,"default": "false",
                            "description": "escludere l'SSLv3"} ),
            ( "ssl_check_certificate", {"type": "bool","mandatory": False,"default": "true",
                                        "description": u"verificare la validità del certificato ssl"} ),
            ( "ssl_client_key", {"type": "str","mandatory": False,"default": "",
                                 "description": "chiave per autenticazione del client"} ),
            ( "ssl_client_cert", {"type": "str","mandatory": False,"default": "",
                                  "description": "certificato per autenticazione del client"} ),
            ( "ssl_cipher", {"type": "str","mandatory": False,"default": "",
                             "description": "tipi di crittografia ammessi (in formato openssl)"} ),
        ] )
        

        return "200 OK",context

class EnvironPage(TemplatePage):
    template_name=config.TEMPLATE_NAMES["environ"]
    page_title="environment"

    def elab(self,context,environ):
        local_environ=collections.OrderedDict()
        keys=environ.keys()
        keys.sort()
        for k in keys:
            local_environ[k]=environ[k]
        if not local_environ["PATH_INFO"].endswith("/"):
            local_environ["PATH_INFO"]+="/"

        context["environ"]=local_environ
        return "200 OK",context

class Error404Page(TemplatePage):
    template_name=config.TEMPLATE_NAMES["404"]

    def __init__(self,path,settings):
        self.path=path
        TemplatePage.__init__(self,settings)

    def elab(self,context,environ):
        context["path"]=self.path
        return "404 Not Found",context

class Error500Page(TemplatePage):
    template_name=config.TEMPLATE_NAMES["500"]

    def __init__(self,exception,settings):
        self.exception=exception
        TemplatePage.__init__(self,settings)

    def elab(self,context,environ):
        context["error"]=unicode(self.exception)
        return "500 Internal Server Error",context

class ActionPage(TemplatePage):
    def __init__(self,settings): 
        TemplatePage.__init__(self,settings)
        self.action_map={ "default": self.default }

    def elab(self,context,environ):
        query_dict={}
        if environ["QUERY_STRING"]:
            query_list=environ["QUERY_STRING"].split("&")
            for l in query_list:
                t=l.split("=")
                if len(t)!=2:
                    continue
                query_dict[t[0]]=t[1]
        if "action" in query_dict.keys():
            action=query_dict["action"]
        else:
            action="default"
        context["action"]=action
        if not action in self.action_map.keys():
            action="default"
        return self.action_map[action](context,environ)

    def default(self,context,environ):
        return "200 OK",context

class TestPage(ActionPage):
    template_name=config.TEMPLATE_NAMES["test"]

    def __init__(self,test_name,settings): 
        self.test_name=test_name
        ActionPage.__init__(self,settings)

    def get_title(self):
        return self.settings.title+": "+self.settings.url_defs[self.test_name].title

    def default(self,context,environ):
        context["settings"]= self.settings
        context["test_name"]= self.test_name
        context["test_description"]= self.settings.url_defs[self.test_name]
        tester_obj=tester.tester_factory(self.settings,self.test_name)
        test_response=tester_obj.execute()
        context["test_response"]=test_response
        context["test_status"]=self.settings.url_defs[self.test_name].check_status(test_response.status)
        return "200 OK",context

class HomePage(ActionPage):
    template_name=config.TEMPLATE_NAMES["homepage"]

    def default(self,context,environ):
        context["settings"]= self.settings
        test_manager=tester.TestManager(self.settings)
        test_time,res_collection=test_manager.run_threaded()
        context["test_time"]=test_time
        context["res_collection"]=res_collection

        for testname,obj in res_collection.items():
            print testname,type(obj["response"].msg),obj["response"].msg

        return "200 OK",context

class RequestHandler(wsgiref.simple_server.WSGIRequestHandler):

    def log_message(self,msg_format,*args):
        my_logger = logging.getLogger(config.LOG_LABEL_ACCESS)
        my_logger.info(msg_format % args)


class UrlTester(object):
    def __init__(self,settings):
        self.settings=settings

    def run_demo(self):
        self._run_http_server(wsgiref.simple_server.demo_app)

    def _run_http_server(self,application):
        # Instantiate the server
        def log_exception_decorator(func,settings):
            def decorated(environ,start_response):
                try:
                    return func(environ,start_response)
                except Exception, e:
                    my_logger = logging.getLogger(config.LOG_LABEL_ERROR)
                    my_logger.exception(e)
                    page=Error500Page(e,settings)
                    response=page.get(environ)
                    start_response(response.status, response.headers)
                    return response.body_iterable
            return decorated
        httpd = wsgiref.simple_server.make_server (
            self.settings.http_host,
            self.settings.http_port,
            log_exception_decorator(application,self.settings),
            handler_class=RequestHandler
        )
        httpd.serve_forever()

    def run_server(self):
        self._run_http_server(self.application)

    def path_map(self,full_path):
        test_list=map(lambda x: "/"+x, self.settings.url_defs.keys() )
        test_list+=map(lambda x: "/"+x+"/", self.settings.url_defs.keys() )

        if not full_path.startswith(self.settings.base_context):
            return Error404Page(full_path,self.settings)
            
        path=full_path[len(self.settings.base_context):]

        if path in ["","/"]:
            return HomePage(self.settings)
        if path in ["/config","/config/"]:
            return ConfigPage(self.settings)
        if path in ["/docs","/docs/"]:
            return DocsPage(self.settings)
        if path in ["/environ","/environ/"]:
            return EnvironPage(self.settings)
        if path in test_list:
            test_name=path.replace("/","")
            return TestPage(test_name,self.settings)
        
        if not self.settings.serve_static: 
            return Error404Page(path,self.settings)

        if path.startswith("/"+config.STATIC_REL_PATH):
            obj_path=path[len(config.STATIC_REL_PATH)+1:]
            return StaticPage(obj_path,self.settings)
        return Error404Page(path,self.settings)

    ####################################
    ### main logic
    def application(self,environ, start_response):
        page=self.path_map(environ["PATH_INFO"])
        response=page.get(environ)
        start_response(response.status, response.headers)
        return response.body_iterable


