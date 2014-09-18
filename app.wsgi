sys.path.insert(0, "/var/www/docroot/horazont/projects/priyomdb2/")

# this sets up the path to teapot
import priyom.config

import teapot
import teapot.wsgi
import teapot.routing

import priyom.api

application = teapot.wsgi.Application(priyom.api.router)
