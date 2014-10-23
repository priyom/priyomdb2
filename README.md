priyom.org Database Backend
===========================

This is the source code of the *next generation* of the [priyom.org][0] database
backend server.

The code is still in development and *not deployed live*. Note that it also
contains parts which are inherently and *intendedly* unsafe (such as the default
login of root:admin). These things will change with deployment, but are handy
for local development.

Dependencies
------------

* Python ≥ 3.3
* sqlalchemy ≥ 0.8
* [teapot with xsltea][1] (recent, i.e. devel branch)
* and probably others :)

   [0]: http://priyom.org
   [1]: https://github.com/zombofant/teapot
