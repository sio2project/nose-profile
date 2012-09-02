"""This plugin will run tests using the cProfile profiler, which is part of the
standard library for Python >= 2.5. To turn it on, use the ``--with-calltree``
option or set the NOSE_WITH_CALLTREE environment variable. Profiler output can
be controlled with the ``--calltree-sort`` and ``--calltree-restrict`` options,
and the profiler output file may be changed with ``--calltree-stats-file``.

Profile output format is compatible with KCacheGrind.

See the `hotshot documentation`_ in the standard library documentation for
more details on the various output options.

.. _hotshot documentation: http://docs.python.org/library/hotshot.html
"""

import optparse
import os
import os.path
import sys
import logging
import tempfile

try:
    import cProfile, pstats
except ImportError:
    cProfile, pstats = None, None

from nose.plugins.base import Plugin
from nose.util import tolist

from kcachegrind import KCacheGrind

# Following code is based on 
# http://somethingaboutorange.com/mrl/projects/nose/0.11.1/plugins/prof.html

log = logging.getLogger('nose.plugins')

class CallTree(Plugin):
    """
    Use this plugin to run tests using the hotshot profiler. 
    """
    pfile = None
    clean_stats_file = False
    def options(self, parser, env):
        """Register commandline options.
        """
        if not self.available():
            return
        Plugin.options(self, parser, env)
        parser.add_option('--calltree-sort', action='store', dest='calltree_sort',
                          default=env.get('NOSE_CALLTREE_SORT', 'cumulative'),
                          metavar="SORT",
                          help="Set sort order for profiler output")
        parser.add_option('--calltree-stats-file', action='store',
                          dest='calltree_stats_file',
                          metavar="FILE",
                          default=env.get('NOSE_CALLTREE_STATS_FILE'),
                          help='Profiler stats file; default is a new '
                          'temp file on each run')
        parser.add_option('--calltree-restrict', action='append',
                          dest='calltree_restrict',
                          metavar="RESTRICT",
                          default=env.get('NOSE_CALLTREE_RESTRICT'),
                          help="Restrict profiler output. See help for "
                          "pstats.Stats for details")

    def available(cls):
        return cProfile is not None
    available = classmethod(available)

    def begin(self):
        """Create profile stats file and load profiler.
        """
        if not self.available():
            return
        self.prof = cProfile.Profile()

    def configure(self, options, conf):
        """Configure plugin.
        """
        if not self.available():
            self.enabled = False
            return
        Plugin.configure(self, options, conf)
        self.conf = conf
        if options.calltree_stats_file:
            self.pfile = os.path.abspath(options.calltree_stats_file)
            self.clean_stats_file = False
        else:
            self.pfile = None
            self.clean_stats_file = True
        self.fileno = None
        self.sort = options.calltree_sort
        self.restrict = tolist(options.calltree_restrict)

    def prepareTest(self, test):
        """Wrap entire test run in :func:`prof.runcall`.
        """
        if not self.available():
            return
        log.debug('preparing test %s' % test)
        def run_and_profile(result, prof=self.prof, test=test):
            prof.runcall(test, result)
        return run_and_profile

    def report(self, stream):
        """Output profiler report.
        """

        log.debug('saving calltree file')

        self._create_pfile()
        calltree_writer = KCacheGrind([self.prof])
        calltree_writer.output(file(self.pfile, 'w'))

        log.debug('printing profiler report')

        prof_stats = pstats.Stats(self.prof)
        prof_stats.sort_stats(self.sort)
        prof_stats.stream = stream

        if self.restrict:
            log.debug('setting profiler restriction to %s', self.restrict)
            prof_stats.print_stats(*self.restrict)
        else:
            prof_stats.print_stats()

    def finalize(self, result):
        """Clean up stats file, if configured to do so.
        """
        if not self.available():
            return
        try:
            self.prof.close()
        except AttributeError:
            # TODO: is this trying to catch just the case where not
            # hasattr(self.prof, "close")?  If so, the function call should be
            # moved out of the try: suite.
            pass
        if self.clean_stats_file:
            if self.fileno:
                try:
                    os.close(self.fileno)
                except OSError:
                    pass
            try:
                os.unlink(self.pfile)
            except OSError:
                pass
        return None

    def _create_pfile(self):
        if not self.pfile:
            self.fileno, self.pfile = tempfile.mkstemp()
            self.clean_stats_file = True
