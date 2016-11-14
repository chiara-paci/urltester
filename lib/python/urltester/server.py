# Python's bundled WSGI server
import wsgiref.simple_server
import config
import random
import jinja2

class Response(object):
    def __init__(self):
        self.body=u""
        self.headers = [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(self.body)))
        ]

    def finalize_headers(self):
        new_headers=[]
        for k,val in self.headers:
            if k!="Content-Length":
                new_headers.append( (k,val) )
            new_headers.append( ('Content-Length', str(len(self.body))) )
        self.headers=new_headers

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

    def my_errors_http_404(self,path):

        status="404 Not Found"

        response_body=u""
        response_body+=u"<p>The requested URL "+path+" was not found on this server.</p>\n"
        response_body+=u"<hr>\n"
        response_body+=u"<address>"+self.settings.title+u"/"+self.settings.version+u"</address>\n"

        response_body=self.build_page("404 Not Found",response_body)

        response_headers = [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Length', str(len(response_body)))
        ]

        return status,response_headers,response_body

    def build_page(self,title,body):
        response_body=u""
        response_body+=u'<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n'
        response_body+=u"<html><head>\n"
        response_body+=u"<title>"+title+u"</title>\n"
        response_body+=u"</head><body>\n"
        response_body+=u"<h1>"+title+u"</h1>\n"
        response_body+=body
        response_body+=u"</body></html>\n"

        response_body=response_body.encode("utf-8")

        return response_body

    def apply_template(self,template_name,context):
        env=jinja2.Environment(loader=jinja2.FileSystemLoader(self.settings.template_dir))
        template=env.get_template(template_name)
        T=template.render(**context)
        T=T.encode('utf-8')
        return T

    def get_response_test(self,test_name,environ):
        response=Response()
        response_body = u'\n<ul>\n'
        for k in [ "REQUEST_METHOD","SCRIPT_NAME","PATH_INFO","QUERY_STRING","SERVER_PROTOCOL","CONTENT_TYPE" ]:
            if environ.has_key(k):
                response_body+= u"<li>"+k+u":"+environ[k]+u"</li>\n"
        response_body+=u"</ul>\n"

        response.body=self.build_page(test_name,response_body)
        return response

    def get_response_homepage(self,environ):
        response=Response()
        response_body = u'\n<ul>\n'
        for k in [ "REQUEST_METHOD","SCRIPT_NAME","PATH_INFO","QUERY_STRING","SERVER_PROTOCOL","CONTENT_TYPE" ]:
            if environ.has_key(k):
                response_body+= u"<li>"+k+u":"+environ[k]+u"</li>\n"
        response_body+=u"</ul>\n"

        response.body=self.build_page(self.settings.title,response_body)
        return response
        pass

    def get_response_config(self,environ):
        response=Response()
        response_body = u'\n<ul>\n'
        response_body+=u"</ul>\n"

        response.body=self.build_page("Config",response_body)
        return response

    def get_response_environ(self,environ):
        response=Response()
        response_body = u'\n<ul>\n'
        for k in [ "REQUEST_METHOD","SCRIPT_NAME","PATH_INFO","QUERY_STRING","SERVER_PROTOCOL","CONTENT_TYPE" ]:
            if environ.has_key(k):
                response_body+= u"<li>"+k+u":"+environ[k]+u"</li>\n"
        response_body+=u"</ul>\n"

        response.body=self.build_page("Environ",response_body)
        return response

    

    ####################################
    ### main logic
    def application(self,environ, start_response):

        test_list=map(lambda x: "/"+x, self.settings.url_defs.keys() )
        test_list+=map(lambda x: "/"+x+"/", self.settings.url_defs.keys() )

        if environ["PATH_INFO"] in test_list:
            status = '200 OK'
            response=self.get_response_test(environ["PATH_INFO"].replace("/","").strip(),environ)
        elif environ["PATH_INFO"] in[ "", "/" ]:
            status = '200 OK'
            response=self.get_response_homepage(environ)
        elif environ["PATH_INFO"] in [ "/config","/config/"]:
            status = '200 OK'
            response=self.get_response_config(environ)
        elif environ["PATH_INFO"] in ["/environ","/environ/" ]:
            status = '200 OK'
            response=self.get_response_environ(environ)
        else:
            status = '404 Not Found'
            status,response_headers,response_body=self.my_errors_http_404(environ["PATH_INFO"])
            start_response(status, response_headers)
            return [response_body]

        response.finalize_headers()
        response_headers=response.headers
        response_body=response.body

        start_response(status, response_headers)
        return [response_body]


