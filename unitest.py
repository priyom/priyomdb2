#!/usr/bin/python2
# encoding=utf8
# File name: unitest.py
# This file is part of: pyuni
#
# LICENSE
#
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
# the License for the specific language governing rights and limitations
# under the License.
#
# Alternatively, the contents of this file may be used under the terms
# of the GNU General Public license (the  "GPL License"), in which case
# the provisions of GPL License are applicable instead of those above.
#
# FEEDBACK & QUESTIONS
#
# For feedback and questions about pyuni please e-mail one of the
# authors named in the AUTHORS file.
########################################################################
from __future__ import unicode_literals, print_function, division
from our_future import *

class Colors(object):
    # HEADER = '\033[95m'
    
    Header = '\033[01m'
    Warning = '\033[93m'
    Success = '\033[01;32m' 
    Skipped = '\033[94m'
    Error = '\033[01;31m'
    Failure = Error
    UnexpectedSuccess = Warning
    ExpectedFailure = Warning
    TestClass = Header
    TestName = Header
    Reset = '\033[0m'

    def disable(self):
        self.Success = ''
        self.Skipped = ''
        self.Failure = ''
        self.Error = ''
        self.UnexpectedSuccess = ''
        self.ExpectedFailure = ''
        self.TestClass = ''
        self.TestName = ''
        self.Reset = ''
        self.Header = ''
        self.Warning = ''
    
    def __call__(self, string, colour):
        return "{0}{2}{1}".format(colour, self.Reset, string)

import unittest
from unittest.util import strclass
import os
import sys
import traceback
import argparse
import textwrap
import itertools
import platform
import time

if platform.python_implementation() == "PyPy":
    import numpypy

STATE_PASS = 0
STATE_SKIP = 1
STATE_ERROR = 2
STATE_FAILURE = 3
STATE_UNEXPECTED_SUCCESS = 4
STATE_EXPECTED_FAILURE = 5

ttyWidth = 80
haveTTY = os.isatty(sys.stdout.fileno())
if haveTTY:
    rows, cols = os.popen('stty size', 'r').read().split()
    ttyWidth = int(cols)

epilog = """Please note that for the reason of auto discovery, all modules which match the glob PATTERN will be imported first. For further information see <http://docs.python.org/library/unittest.html#test-discovery>.

This script will return a status code corresponding to the status of the test suite.

0 => All tests successful.
1 => At least one test skipped
2 => At least one test failed expectedly
3 => At least one test succeeded unexpectedly
4 => At least one test failed unexpectedly
5 => At least one test errored
6 => Should never happen. If you encounter this, report a bug.
7 => No tests were found.
"""
epilog = "\n".join(itertools.chain(*(textwrap.wrap(line, width=80) if len(line) > 0 else (line,) for line in epilog.split("\n"))))

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="Run auto-discovered unit tests inside the current directory.",
    epilog=epilog
)
parser.add_argument(
    "--pattern", "-p",
    metavar="PATTERN",
    type=unicode,
    default="test_*.py",
    help="Set a glob pattern for unit-test files. Default is test_*.py",
    dest="pattern",
)
parser.add_argument(
    "--colors", "-c",
    choices=["auto", "on", "off"],
    default="auto",
    help="Whether to use colors. auto, the default, checks whether stdout is a tty. If so, colors are used.",
    dest="colors",
)
parser.add_argument(
    "--width", "-w",
    default=ttyWidth,
    type=int,
    help="Terminal width. This is auto-detected on most systems and defaults to 80 if auto-detection fails and no other value is given.",
    dest="ttyWidth"
)
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "--strip-module-prefix",
    default="test_",
    metavar="PREFIX",
    type=unicode,
    help="Set a prefix which will be stripped from the test module names. This defaults to test_",
    dest="stripModulePrefix"
)
group.add_argument(
    "--no-strip-module-prefix", 
    dest="stripModulePrefix",
    action="store_const",
    const="",
    help="Disable stripping of the module name."
)
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "--strip-method-prefix",
    default="test_",
    metavar="PREFIX",
    type=unicode,
    help="Set a prefix which will be stripped from the test method names. This defaults to test_",
    dest="stripMethodPrefix"
)
group.add_argument(
    "--no-strip-method-prefix", 
    dest="stripMethodPrefix",
    action="store_const",
    const="",
    help="Disable stripping of the module name."
)
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "--no-stats",
    dest="noStats",
    action="store_true",
    default=False,
    help="Disable summarizing stats."
)
group.add_argument(
    "--force-stats", "-f",
    dest="forceStats",
    action="store_true",
    default=False,
    help="Print stats even if quiet is enabled."
)
parser.add_argument(
    "--quiet", "-q",
    dest="quiet",
    action="store_true",
    help="Disable stats and informational output; If any test fails, the test, state and traceback is printed to stderr."
)
parser.add_argument(
    "--start-at", "-o",
    dest="onlySubDir",
    type=unicode,
    metavar="DIR",
    default=os.getcwd(),
    help="Start test discovery at DIR. Defaults to . (current directory)"
)
parser.add_argument(
    "--project-dir", 
    dest="projectDir",
    type=unicode,
    metavar="DIR",
    default=os.getcwd(),
    help="Set the project directory to DIR; This is important for imports to work correctly. Defaults to . (current directory)"
)
parser.add_argument(
    "--stderr",
    dest="stderr",
    action="store_true",
    default=False,
    help="Print statistics to stderr instead of stdout; This is useful to separate unittest output from wrapper script output."
)
args = parser.parse_args()

Colors = Colors()
if args.colors == "off" or (args.colors == "auto" and not haveTTY):
    Colors.disable()

loader = unittest.TestLoader()

class AwesomeTextResult(unittest.TestResult):
    testNoteIndent = "        "
    stateNames = [
        ("ok",                  Colors.Success),
        ("skipped",             Colors.Skipped),
        ("error",               Colors.Error),
        ("failure",             Colors.Failure),
        ("unexpected success",  Colors.UnexpectedSuccess),
        ("expected failure",    Colors.ExpectedFailure)
    ]
    maxStateNameLen = len(stateNames[STATE_UNEXPECTED_SUCCESS][0])
    ttyWidth = 80
    
    def __init__(self, ttyWidth, quiet, stripModulePrefix, stripMethodPrefix, *args, **kwargs):
        super(AwesomeTextResult, self).__init__(*args, **kwargs)
        self._previousPath = None
        self.ttyWidth = ttyWidth
        self.success = []
        self.quiet = quiet
        self.stripModulePrefix = stripModulePrefix
        self.stripMethodPrefix = stripMethodPrefix

    def _strip(self, name, s):
        l = len(s)
        if l == 0:
            return name
        if name[:l] == s:
            return name[l:]
        else:
            return name

    def _extractModuleAndMethodName(self, test):
        try:
            methodName = test._testMethodName
        except AttributeError:
            methodName = str(test).partition(" ")[0]
        if methodName == "runTest":
            methodName = None
        else:
            methodName = self._strip(methodName, self.stripMethodPrefix)
        modulePath = type(test).__module__.split(".")
        modulePath[-1] = self._strip(modulePath[-1], self.stripModulePrefix)
        modulePath.append(type(test).__name__)
        return (modulePath, methodName)
        
    def _formatTestName(self, name, indent=" "*2, color=Colors.TestName):
        testNameLen = self.ttyWidth - (self.maxStateNameLen + (len(indent+" $")) - (len(color) + len(Colors.Reset)))
        return ("{1}{0:.<"+unicode(testNameLen)+"s} ").format(Colors(name, color)+" ", indent)
    
    def _printTestName(self, test):
        modulePath, methodName = self._extractModuleAndMethodName(test)
        if methodName is None:
            print(self._formatTestName(".".join(modulePath), "", Colors.TestClass), end='')
            self.testNoteIndent = " "*4
        else:
            if self._previousPath != modulePath:
                self._previousPath = modulePath
                print("{0}:".format(Colors(".".join(modulePath), Colors.TestClass)))
            print(self._formatTestName(methodName), end='')
            self.testNoteIndent = " "*6

    def _formatPlainFullTestName(self, test):
        modulePath, methodName = self._extractModuleAndMethodName(test)
        if methodName is None:
            methodName = "runTest"
        modulePath.append(methodName)
        return ".".join(modulePath)
    
    def _printState(self, state):
        print(Colors(*self.stateNames[state]))

    def _skipBlank(self, s):
        for line in s.split("\n"):
            line = line.rstrip()
            if len(line) > 0:
                yield line

    def _indented(self, s, indent=None):
        indent = indent if indent is not None else self.testNoteIndent
        return indent + (("\n"+indent).join(self._skipBlank(s)))

    def _formatError(self, err, indent=None):
        s = "".join(traceback.format_exception(*err))
        return self._indented(s, indent)
    
    def startTest(self, test):
        if not self.quiet:
            self._printTestName(test)
        super(AwesomeTextResult, self).startTest(test)
    
    def addError(self, test, err):
        super(AwesomeTextResult, self).addError(test, err)
        if self.quiet:
            print("Test case {0} errored:".format(self._formatPlainFullTestName(test)), file=sys.stderr)
            print(self._formatError(err, indent=""), file=sys.stderr)
        else:
            print(Colors("error", Colors.Error))
            print(self._formatError(err), file=sys.stderr)

    def addFailure(self, test, err):
        super(AwesomeTextResult, self).addFailure(test, err)
        if self.quiet:
            print("Test case {0} failed:".format(self._formatPlainFullTestName(test)), file=sys.stderr)
            print(self._formatError(err, indent=""), file=sys.stderr)
        else:
            print(Colors("failure", Colors.Failure))
            print(self._formatError(err), file=sys.stderr)

    def addSuccess(self, test):
        super(AwesomeTextResult, self).addSuccess(test)
        self.success.append(test)
        if not self.quiet:
            print(Colors("ok", Colors.Success))

    def addSkip(self, test, reason):
        super(AwesomeTextResult, self).addSkip(test, reason)
        if not self.quiet:
            print(Colors("skip", Colors.Error))
            print(self.testNoteIndent+reason)
        else:
            print("Test case {0} skipped: {1}".format(self._formatPlainFullTestName(test), reason), file=sys.stderr)

    def addExpectedFailure(self, test, err):
        super(AwesomeTextResult, self).addExpectedFailure(test, err)
        if self.quiet:
            print("Test case {0} failed expectedly:".format(self._formatPlainFullTestName(test)), file=sys.stderr)
            print(self._formatError(err, indent=""), file=sys.stderr)
        else:
            print(Colors("expected failure", Colors.ExpectedFailure))
            print(self._formatError(err), file=sys.stderr)

    def addUnexpectedSuccess(self, test):
        super(AwesomeTextResult, self).addUnexpectedSuccess(test)
        if self.quiet:
            print("Test case {0} succeeded unexpectedly.".format(self._formatPlainFullTestName(test)), file=sys.stderr)
        else:
            print(Colors("unexpected success", Colors.UnexpectedSuccess))

    def _colouredNumber(self, count, nonZero="", zero=""):
        return Colors(unicode(count), zero if count == 0 else nonZero)

    def getStats(self, suite):
        passedCount = len(self.success)
        errorCount = len(self.errors)
        failureCount = len(self.failures)
        skippedCount = len(self.skipped)
        expectedFailureCount = len(self.expectedFailures)
        unexpectedSuccessCount = len(self.unexpectedSuccesses)
        testsTotal = suite.countTestCases()
        return passedCount, errorCount, failureCount, skippedCount, expectedFailureCount, unexpectedSuccessCount, testsTotal

    def printStats(self, stats, file=sys.stdout):
        passedCount, errorCount, failureCount, skippedCount, expectedFailureCount, unexpectedSuccessCount, testsTotal = stats

        passedColour = Colors.Warning
        if passedCount == self.testsRun:
            passedColour = Colors.Success
        elif passedCount == 0:
            passedColour = Colors.Failure
        
        
        print("{0} ({1} tests in total):".format(Colors("Statistics", Colors.Header), testsTotal), file=file)
        print("  passed                 : {0}".format(Colors(passedCount, passedColour)), file=file)
        print("  skipped                : {0}".format(self._colouredNumber(skippedCount, Colors.Skipped, Colors.Success)), file=file)
        print("  expected failures      : {0}".format(self._colouredNumber(expectedFailureCount, Colors.ExpectedFailure, Colors.Success)), file=file)
        print("  unexpected successes   : {0}".format(self._colouredNumber(unexpectedSuccessCount, Colors.UnexpectedSuccess, Colors.Success)), file=file)
        print("  errors                 : {0}".format(self._colouredNumber(errorCount, Colors.Error, Colors.Success)), file=file)
        print("  failures               : {0}".format(self._colouredNumber(failureCount, Colors.Failure, Colors.Success)), file=file)
        print("  ran                    : {0}".format(Colors(self.testsRun, Colors.Success if self.testsRun == testsTotal else Colors.Warning)), file=file)

results = AwesomeTextResult(args.ttyWidth, args.quiet, args.stripModulePrefix, args.stripMethodPrefix)
results.ttyWidth = ttyWidth
tests = loader.discover(args.onlySubDir, args.pattern, args.projectDir)
if tests.countTestCases() == 0:
    print("unitest.py: error: no tests found", file=sys.stderr)
    sys.exit(7)
if not args.quiet:
    print("Running {0} unittests (detected from auto-discovery)".format(tests.countTestCases()))
startTime = time.time()
tests.run(results)
endTime = time.time()
stats = results.getStats(tests)
if args.forceStats or not args.quiet:
    if args.stderr:
        Colors.disable()
    if not args.noStats:
        results.printStats(stats, file=(sys.stderr if args.stderr else sys.stdout))
    print("Ran {2} tests on {0} in {1} seconds".format(
        Colors(platform.python_implementation(), Colors.Header),
        Colors("{0:.6f}".format(endTime-startTime), Colors.Header),
        Colors(results.testsRun, Colors.Header)
        ),
        file=(sys.stderr if args.stderr else sys.stdout)
    )

# determine the exit code
passedCount, errorCount, failureCount, skippedCount, expectedFailureCount, unexpectedSuccessCount, testsTotal = stats
tmpCount = passedCount
if tmpCount == testsTotal:
    sys.exit(0)
tmpCount += skippedCount
if tmpCount == testsTotal:
    sys.exit(1)
tmpCount += expectedFailureCount
if tmpCount == testsTotal:
    sys.exit(2)
tmpCount += unexpectedSuccessCount
if tmpCount == testsTotal:
    sys.exit(3)
tmpCount += failureCount
if tmpCount == testsTotal:
    sys.exit(4)
tmpCount += errorCount
if tmpCount == testsTotal:
    sys.exit(5)
sys.exit(6) # this should never ever happen
