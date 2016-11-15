#! /usr/bin/env python

import sys
import os

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

sys.path.append(PARENT_DIR+"/lib/python")

import urltester.config
import urltester.server

settings=urltester.config.Settings(paths=[
    "/home/chiara/urltester/tests/real_test_corretti.conf",
    "/home/chiara/urltester/tests/real_test_errori_socket.conf",
    "/home/chiara/urltester/tests/real_test_errori_ssl.conf",
])

urltester=urltester.server.UrlTester(settings)

application=urltester.application
