import sys
sys.path.insert(0, "/var/www/docroot/horazont/projects/teapot/")

import teapot
import teapot.wsgi
import teapot.routing

sys.path.insert(0, "/var/www/docroot/horazont/projects/priyomdb2/")

import priyom.config
priyom.config.base_path = "/var/www/docroot/horazont/projects/priyomdb2/"
priyom.config.recalc_paths()

import priyom.api

application = teapot.wsgi.Application(priyom.api.router)
