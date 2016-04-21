###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Tavendo GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

from os import environ
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from threading import Thread

from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner

res=None

class RPC_caller(ApplicationSession):


    @inlineCallbacks
    def onJoin(self, details):
        print("session attached")

        yield self.call(u'com.arguments.ping')
        print("Pinged!")
        
    def onDisconnect(self):
        print("disconnected")
        #reactor.stop()

class WampCall():
    def __init__(self):
        self.runner = ApplicationRunner(u"ws://127.0.0.1:8181/ws",u"s4t",
        # debug=False,  # optional; log even more details
        installSignalHandlers=False
        )
        self.t=Thread(target=self.runner.run, args=(RPC_caller,))
        self.t.daemon=True

    def start_th(self):
        print 'start'
        self.t.start()   
             
    def get(self):
        extra={'name':name,'args': args},
        global res
        r=res
        res=None
        return r
    
if __name__ == '__main__':
    r=WampCall()
    r.start_th()
    print 'ooooo'
