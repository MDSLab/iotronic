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
import multiprocessing
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
from oslo_log import log
from oslo_config import cfg
from multiprocessing import Pipe

import time

LOG = log.getLogger(__name__)

wamp_opts = [
    cfg.StrOpt('wamp_ip',
               default='127.0.0.1',
               help=('URL of wamp broker')),
    cfg.IntOpt('wamp_port',
               default=8181,
               help='port wamp broker'),
    cfg.StrOpt('wamp_realm',
               default='s4t',
               help=('realm broker')),
]
CONF = cfg.CONF
CONF.register_opts(wamp_opts, 'wamp')


class RPCWampManager(ApplicationSession):
    """
    An application component calling the different backend procedures.
    """

    @inlineCallbacks
    def onJoin(self, details):
        print("session attached")
        rpc=self.config.extra['rpc']
        self.pipe_out=self.config.extra['pipe']
        res = yield self.call(rpc)
        self.pipe_out.send(format(res))
        print("res: {}".format(res))
        self.leave()

    def onDisconnect(self):
        print("disconnected")
        reactor.stop()

class RPCWampClient:
    def __init__(self,ip,port,realm,rpc,b_a_ext):
        self.ip=unicode(ip)
        self.port=unicode(port)
        self.realm=unicode(realm)
        self._url = "ws://"+self.ip+":"+self.port+"/ws"
        self.runner = ApplicationRunner(url=unicode(self._url), realm=self.realm, extra={'rpc':rpc,'pipe':b_a_ext}
                                        #debug=True, debug_wamp=True, debug_app=True
                                        )
        self.runner.run(RPCWampManager, start_reactor=False)

class RPC_Wamp_Client(object):    
    
    def __init__(self,rpc):
        self.ip=unicode(CONF.wamp.wamp_ip)
        self.port=unicode(CONF.wamp.wamp_port)
        self.realm=unicode(CONF.wamp.wamp_realm)        
        self.b_a_int, b_a_ext = Pipe()
        self.client = RPCWampClient(self.ip,self.port,self.realm,rpc,b_a_ext)
        self.multi = multiprocessing.Process(target=reactor.run,args=())        

        
    def rpc_call(self):
        try: 
            self.multi.start()
        except:
            pass
        x=''
        while True:
            if self.b_a_int.poll():
                x= self.b_a_int.recv()
                self.multi.join()
                break
                
        return x

