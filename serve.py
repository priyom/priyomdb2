#!/usr/bin/python3

if __name__ == "__main__":
    import argparse
    import logging
    import sys

    import tornado.wsgi
    import tornado.httpserver
    import tornado.ioloop

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f", "--app-file",
        default="app.wsgi")
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8080)
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        dest="verbosity",
        default=0)

    args = parser.parse_args()
    sys.argv[:] = []

    logging.basicConfig(level=logging.ERROR, format='%(levelname)-8s %(message)s')
    if args.verbosity >= 3:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.verbosity >= 2:
        logging.getLogger().setLevel(logging.INFO)
    elif args.verbosity >= 1:
        logging.getLogger().setLevel(logging.WARNING)

    with open(args.app_file, "r") as f:
        code = compile(f.read(), args.app_file, 'exec')

    locals_dict = {}
    exec(code, globals(), locals_dict)

    container = tornado.wsgi.WSGIContainer(locals_dict["application"])
    server = tornado.httpserver.HTTPServer(container)
    server.listen(args.port)

    print("serving on port {}".format(args.port))
    tornado.ioloop.IOLoop.instance().start()
