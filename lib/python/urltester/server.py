# Python's bundled WSGI server
import wsgiref.simple_server

class UrlTester(object):
    def __init__(self,settings):
        self.settings=settings


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
            application
        )
        
        # Wait for a single request, serve it and quit
        httpd.serve_forever()

