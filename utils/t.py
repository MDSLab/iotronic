from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import multiprocessing

from oslo_log import log
from oslo_config import cfg


from twisted.internet import reactor


from multiprocessing import Pipe, Pool
import threading

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

class RPCWampServerManager(ApplicationSession):
    
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        LOG.info("RPC wamp manager created")
        
    '''
    #unused methods
    def onConnect(self):
        print("transport connected")
        self.join(self.config.realm)

    def onChallenge(self, challenge):
        print("authentication challenge received")

    def onLeave(self, details):
        print("session left")
        import os, signal
        os.kill(multi.pid, signal.SIGKILL)
        
    def onDisconnect(self):
        print("transport disconnected")
    '''
    
    @inlineCallbacks
    def onJoin(self, details):
        LOG.info('RPC Wamp Session ready')
        import iotronic.wamp.functions as fun
        self.subscribe(fun.leave_function, 'wamp.session.on_leave')

        try:
            yield self.register(fun.test, u'stack4things.test')
            yield self.register(fun.registration, u'stack4things.register')
            yield self.register(fun.registration_uuid, u'stack4things.register_uuid')
            
            LOG.info("Procedures registered")
        except Exception as e:
            print("could not register procedure: {0}".format(e))
            
class RPCWampServer:
    def __init__(self,ip,port,realm):
        self.ip=unicode(ip)
        self.port=unicode(port)
        self.realm=unicode(realm)
        self._url = "ws://"+self.ip+":"+self.port+"/ws"
        from twisted.internet import reactor
        self.runner = ApplicationRunner(url=unicode(self._url), realm=self.realm,
                                        #debug=True, debug_wamp=True, debug_app=True
                                        )
        self.runner.run(RPCWampServerManager, start_reactor=False)
        
        
class RPCWampManagerClient(ApplicationSession):
    """
    An application component calling the different backend procedures.
    """

    @inlineCallbacks
    def onJoin(self, details):
        #print("session attached")
        rpc=self.config.extra['rpc']
        self.pipe_out=self.config.extra['pipe']
        res = yield self.call(rpc)
        self.pipe_out.send(format(res))
        #print("res: {}".format(res))
        self.leave()

    def onDisconnect(self):
        #print("disconnected")
        reactor.stop()

class RPCWampClient:
    def __init__(self,ip,port,realm,rpc,b_a_ext):
        self.ip=unicode(ip)
        self.port=unicode(port)
        self.realm=unicode(realm)
        self._url = "ws://"+self.ip+":"+self.port+"/ws"
        from twisted.internet import reactor
        self.runner = ApplicationRunner(url=unicode(self._url), realm=self.realm, extra={'rpc':rpc,'pipe':b_a_ext},
                                        debug=False, debug_wamp=True, debug_app=True
                                        )
        self.runner.run(RPCWampManagerClient, start_reactor=False)

        
        
class RPC_Wamp(object):    
    
    def __init__(self):
        self.ip=unicode(CONF.wamp.wamp_ip)
        self.port=unicode(CONF.wamp.wamp_port)
        self.realm=unicode(CONF.wamp.wamp_realm)
        self.server = RPCWampServer(self.ip,self.port,self.realm)
        self.b_a_int, self.b_a_ext = Pipe()
        server_process = multiprocessing.Process(target=reactor.run,args=())
        server_process.start()
        
        
    def rpc_call(self,rpc):
        x=''
        client = RPCWampClient(self.ip,self.port,self.realm,rpc,self.b_a_ext)
        client_process = multiprocessing.Process(target=reactor.run,args=())
        client_process.start()
    
        while True:
            if self.b_a_int.poll():
                x= self.b_a_int.recv()
                client_process.join()
                break
              
        return x
        
o=RPC_Wamp()

import time
while True:
    time.sleep(2)
    print o.rpc_call(u'stack4things.test')
        
