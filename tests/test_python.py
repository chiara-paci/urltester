#!/usr/bin/env python

import collections
import HTMLParser
import httplib
import json
import os
import random
import re
import socket
import ssl
import string
import sys
import threading
import time
import unittest
import urllib2
import wsgiref.simple_server

try:
    import jinja2
except Exception, e:
    print "No jinja2"

