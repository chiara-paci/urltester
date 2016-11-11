#! /usr/bin/env python

import argparse
import sys
import os

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

print PARENT_DIR+"/lib/python"

sys.path.append(PARENT_DIR+"/lib/python")
import urltester.config


# Python's bundled WSGI server
from wsgiref.simple_server import make_server

def application (environ, start_response):

    # Sorting and stringifying the environment key, value pairs
    response_body = 'Ciao\n'.join(response_body)

    status = '200 OK'
    response_headers = [
        ('Content-Type', 'text/plain'),
        ('Content-Length', str(len(response_body)))
    ]
    start_response(status, response_headers)

    return [response_body]

parser = argparse.ArgumentParser(description="UrlTester Server")
parser.add_argument("-v","--version", action="version", version="UrlTester Server "+urltester.config.VERSION)

args=parser.parse_args(sys.argv[1:])


# Instantiate the server
httpd = make_server (
    'localhost', # The host name
    9876, # A port number where to wait for the request
    application # The application object name, in this case a function
)

# Wait for a single request, serve it and quit
httpd.serve_forever()
