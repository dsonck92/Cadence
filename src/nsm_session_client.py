#!/usr/bin/env python3
from liblo import make_method, Server
from os import environ, path
from subprocess import Popen, PIPE

haveNsm = path.exists('/usr/bin/nsmd')

class NSMClient(Server):

    @make_method('/reply', None)
    def replyHandler(self, path, args):
        path = args[0]
        args = args[1:]
        print("Path '{}'".format(path))

        if path == '/nsm/server/list':
            self._sessions.append(args[0])
        
    @make_method('/nsm/server/list', 'is')
    def listHandler(self, path, args):
        if args[0] == 0:
            print("List end")
            self._available = True
            print("Sessions: {}".format(self._sessions))

    @make_method(None, None)
    def catchall(self, path, args):
        self._available = True
        print("{} {}".format(path, args))

    def _startNsmDaemon(self):
        if not haveNsm:
            print("Nsm Daemon not available")
            return
        
        print("Starting NSM Daemon...")
        self._nsmd = Popen(['nsmd', '--detach'], stdout=PIPE)
        while self._osc_target is None:
            for line in self._nsmd.stdout:
                line = line.decode('utf-8')
                line.strip()
                print("Line: {}".format(line))
                if line.startswith('NSM_URL='):
                    self._osc_target = line[len('NSM_URL='):]

    def _sendAndRead(self, *args, **kwargs):
        self.send(*args, **kwargs)

        # Keep reading until nothing is available anymore
        while self.recv(500):
            pass


    def __init__(self):
        Server.__init__(self)
        self._osc_target = environ.get('NSM_URL', None)
        self._nsmd = None
        self._available = False
        self._sessions = []

    def check(self):
        if self._osc_target is None:
            # No target, so not available
            self._available = False
        else:
            # Target is available, so probe it
            self.loadSessions()


    def start(self):
        # Start if necessary
        if self._osc_target is None:
            self._startNsmDaemon()
        elif not self._available:
            self.check()
        if not self._available:
            self._startNsmDaemon()

    def isAvailable(self):
        return self._available
    
    def loadSessions(self):
        self._sessions.clear()
        self._sendAndRead(self._osc_target, '/nsm/server/list')

    def getSessions(self):
        return self._sessions

    def startSession(self, session_name):
        print("Opening session: {}".format(session_name))
        self._sendAndRead(self._osc_target, "/nsm/server/open", ('s', session_name))