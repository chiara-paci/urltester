#! /usr/bin/env python

import sys
import os

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

sys.path.append(PARENT_DIR+"/lib/python")

import urltester.config
import urltester.server


settings=urltester.config.Settings()
urltester=urltester.server.UrlTester(settings)

application=urltester.application
