"""Generic Linux daemon base class"""

# Adapted from http://www.jejik.com/files/examples/daemon3x.py
# Thanks to the original author

import os
import gc
import sys
import time
import atexit
import signal
import syslog
import traceback

import psutil


class Daemon(object):
    """A generic daemon class.

    Usage: subclass the daemon class and override the run() method."""
    def __init__(self, pidfile):
        self.pidfile = pidfile

    def daemonize(self):
        """Daemonize class. UNIX double fork mechanism."""
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first parent
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #1 failed: {0}\n'.format(err))
            sys.exit(1)

        # Decouple from parent environment
        os.chdir('/')
        os.setsid()
        os.umask(0)

        # Do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # Exit from second parent
                sys.exit(0)
        except OSError as err:
            sys.stderr.write('fork #2 failed: {0}\n'.format(err))
            sys.exit(1)

        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        stdi = open(os.devnull, 'r')
        stdo = open(os.devnull, 'a+')
        stde = open(os.devnull, 'a+')

        os.dup2(stdi.fileno(), sys.stdin.fileno())
        os.dup2(stdo.fileno(), sys.stdout.fileno())
        os.dup2(stde.fileno(), sys.stderr.fileno())

        # Write pidfile
        atexit.register(self.delpid)

        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as fd:
            fd.write(pid + '\n')

    def delpid(self):
        """Delete pid file"""
        os.remove(self.pidfile)

    def start(self):
        """Start the daemon."""
        # Check for a pidfile to see if the daemon is already running
        try:
            with open(self.pidfile, 'r') as pidf:
                pid = int(pidf.read().strip())
        except IOError:
            pid = None

        if pid:
            message = 'pidfile {0} already exist. Daemon already running?\n'
            sys.stderr.write(message.format(self.pidfile))
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        syslog.syslog(syslog.LOG_INFO, '{}: started'.format(os.path.basename(sys.argv[0])))
        while True:
            # Check if Steam is running
            if not [p for p in psutil.process_iter() if p.name() == 'steam']:
                try:
                    self.run()
                except Exception as e:
                    syslog.syslog(syslog.LOG_ERR, '{}: {!s}'.format(os.path.basename(sys.argv[0]), e))
                    syslog.syslog(syslog.LOG_ERR, traceback.format_exc())
                    gc.collect()
            else:
                syslog.syslog(syslog.LOG_INFO, '{}: steam client is running'.format(os.path.basename(sys.argv[0])))
            time.sleep(2)

    def stop(self):
        """Stop the daemon."""
        # Get the pid from the pidfile
        try:
            with open(self.pidfile, 'r') as pidf:
                pid = int(pidf.read().strip())
        except IOError:
            pid = None

        if not pid:
            message = 'pidfile {0} does not exist. Daemon not running?\n'
            sys.stderr.write(message.format(self.pidfile))
            return  # Not an error in a restart

        # Try killing the daemon process
        try:
            while True:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            e = str(err.args)
            if e.find('No such process') > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print(str(err.args))
                sys.exit(1)
        syslog.syslog(syslog.LOG_INFO, '{}: stopped'.format(os.path.basename(sys.argv[0])))

    def restart(self):
        """Restart the daemon."""
        self.stop()
        self.start()

    def run(self):
        """You should override this method when you subclass Daemon.

        It will be called after the process has been daemonized by start() or restart().
        """
