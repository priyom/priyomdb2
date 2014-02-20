import sys
sys.path.insert(0, "/var/www/docroot/horazont/projects/teapot/")

import teapot
import teapot.wsgi
import teapot.routing

sys.path.insert(0, "/var/www/docroot/horazont/projects/priyomdb2/")

import priyom.api

application = teapot.wsgi.Application(priyom.api.Router(
    database="mysql+mysqlconnector://priyom2@localhost/priyom2?charset=utf8"
))