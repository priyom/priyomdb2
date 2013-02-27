#!/usr/bin/python2
# encoding=utf-8
from __future__ import unicode_literals, print_function

import sys, os, logging

logging.basicConfig(level=logging.INFO)

sys.path.append("/etc")
from webconf.priyomapi import conf
sys.path.remove("/etc")

try:
    sys.path.extend(conf["pythonpath"])
except KeyError:
    pass
os.chdir(conf["datapath"])

import PyXWF.WebBackends.WSGI as WSGI

sitemapFile = os.path.join(conf["datapath"], "sitemap.xml")

application = WSGI.WSGISite(
    sitemapFile,
    default_url_root=conf.get("urlroot")
)
