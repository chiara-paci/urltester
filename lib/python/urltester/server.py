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
            self.application
        )
        
        # Wait for a single request, serve it and quit
        httpd.serve_forever()


    ####################################
    ### main logic
    def application(self,environ, start_response):

        # Sorting and stringifying the environment key, value pairs
        response_body = 'Ciao\n'
        for k in [ "REQUEST_METHOD","SCRIPT_NAME","PATH_INFO","QUERY_STRING","SERVER_PROTOCOL","CONTENT_TYPE" ]:
            if environ.has_key(k):
                response_body+= k+":"+environ[k]+"\n"

        status = '200 OK'
        response_headers = [
            ('Content-Type', 'text/plain'),
            ('Content-Length', str(len(response_body)))
        ]

        start_response(status, response_headers)

        return [response_body]


