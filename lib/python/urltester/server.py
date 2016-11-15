# Python's bundled WSGI server
import wsgiref.simple_server
import random
import jinja2
import collections

import config
import tester

class Response(object):
    def __init__(self):
        self.body=u""
        self.headers = [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(self.body)))
        ]
        self.status="200 OK"

    def finalize_headers(self):
        new_headers=[]
        for k,val in self.headers:
            if k!="Content-Length":
                new_headers.append( (k,val) )
            new_headers.append( ('Content-Length', str(len(self.body))) )
        self.headers=new_headers

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
        context={
            "title": self.get_title(),
            "base_url": environ["SCRIPT_NAME"]
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
    
class HomePage(TemplatePage):
    template_name=config.TEMPLATE_NAMES["homepage"]

    def elab(self,context,environ):
        context["settings"]=self.settings
        return "200 OK",context

class ConfigPage(TemplatePage):
    template_name=config.TEMPLATE_NAMES["config"]
    page_title="configuration"

    def elab(self,context,environ):
        context["settings"]=self.settings
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


class TestPage(TemplatePage):
    template_name=config.TEMPLATE_NAMES["test"]
    
    def __init__(self,test_name,settings): 
        self.test_name=test_name
        TemplatePage.__init__(self,settings)
        self.action_map={ "default": self.default }

    def get_title(self):
        return self.settings.title+": "+self.test_name

    def elab(self,context,environ):
        query_dict={}
        if environ["QUERY_STRING"]:
            query_list=environ["QUERY_STRING"].split("&")
            for l in query_list:
                t=l.split("=")
                if len(t)!=2:
                    continue
                query_dict[t[0]]=t[1]
        context["settings"]= self.settings
        context["test_name"]= self.test_name
        context["test_description"]= self.settings.url_defs[self.test_name]
        if "action" in query_dict.keys():
            action=query_dict["action"]
        else:
            action="default"
        context["action"]=action
        if not action in self.action_map.keys():
            action="default"
        return self.action_map[action](context,environ)

    def default(self,context,environ):
        url=self.settings.url_defs[self.test_name].url
        timeout=self.settings.url_defs[self.test_name].timeout
        tester_obj=tester.Tester(self.test_name,url,timeout)
        test_response=tester_obj.execute()
        context["test_response"]=test_response
        return "200 OK",context

class UrlTester(object):
    def __init__(self,settings):
        self.settings=settings
        self.ut_id=random.choice(range(0,100000))
        print "urltester id:",self.ut_id

    def run_demo(self):
        httpd = wsgiref.simple_server.make_server (
            self.settings.http_host,
            self.settings.http_port,
            wsgiref.simple_server.demo_app
        )
        
        # Wait for a single request, serve it and quit
        httpd.serve_forever()

    def run_server(self):
        # Instantiate the server
        httpd = wsgiref.simple_server.make_server (
            self.settings.http_host,
            self.settings.http_port,
            self.application
        )
        
        httpd.serve_forever()

    def path_map(self,path):
        test_list=map(lambda x: "/"+x, self.settings.url_defs.keys() )
        test_list+=map(lambda x: "/"+x+"/", self.settings.url_defs.keys() )

        if path in ["","/"]:
            return HomePage(self.settings)
        if path in ["/config","/config/"]:
            return ConfigPage(self.settings)
        if path in ["/environ","/environ/"]:
            return EnvironPage(self.settings)
        if path in test_list:
            test_name=path.replace("/","")
            return TestPage(test_name,self.settings)
        return Error404Page(path,self.settings)

    ####################################
    ### main logic
    def application(self,environ, start_response):
        page=self.path_map(environ["PATH_INFO"])
        response=page.get(environ)
        start_response(response.status, response.headers)
        return [response.body]


