from twisted.internet.defer import inlineCallbacks
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner
import multiprocessing
from twisted.internet import reactor
from oslo_log import log
from oslo_config import cfg
from multiprocessing import Pipe
from multiprocessing import Queue
import threading

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
    
    def __init__(self, config=None):
        ApplicationSession.__init__(self, config)
        #print("RPC wamp manager created")
        q_rpc=self.config.extra['queue']
        b_a_ext=self.config.extra['pipe']
        self.q_rpc=q_rpc
        self.pipe_out=b_a_ext
        
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
        
        print('RPC Wamp Session ready')
        import iotronic.wamp.functions as fun
        self.subscribe(fun.leave_function, 'wamp.session.on_leave')

        try:
            yield self.register(fun.test, u'stack4things.test')
            yield self.register(fun.registration, u'stack4things.register')
            yield self.register(fun.registration_uuid, u'stack4things.register_uuid')
            
            print("Procedures registered ")
        except Exception as e:
            print("could not register procedure: {0}".format(e))
            
        while True:
            time.sleep(.01)
            if not self.q_rpc.empty():
                rpc=self.q_rpc.get()
                print rpc
                #print("RPC receved ",format(rpc))
                try:
                    res = yield self.call(rpc,)
                    print("Result: ",format(res))
                    self.pipe_out.send(format(res))
                except Exception as e:
                    print(format(e))


        
            
class RPCWampClient:
    def __init__(self,ip,port,realm,q_rpc,b_a):
        self.ip=unicode(ip)
        self.port=unicode(port)
        self.realm=unicode(realm)
        self._url = "ws://"+self.ip+":"+self.port+"/ws"
        self.runner = ApplicationRunner(url=unicode(self._url), realm=self.realm, extra={'queue':q_rpc,'pipe':b_a}
                                        #debug=True, debug_wamp=True, debug_app=True
                                        )
        self.runner.run(RPCWampManager, start_reactor=False)
        
        
class RPC_Wamp_Client(object):    
    
    def __init__(self):
        self.ip=unicode(CONF.wamp.wamp_ip)
        self.port=unicode(CONF.wamp.wamp_port)
        self.realm=unicode(CONF.wamp.wamp_realm)
        self.q_rpc = Queue()
        self.b_a_int, b_a_ext = Pipe()
        
        
        client = RPCWampClient(self.ip,self.port,self.realm,self.q_rpc,b_a_ext)

        multi = multiprocessing.Process(target=reactor.run,args=())    
        multi.daemon = True    
        multi.start()
        
    def rpc_call(self,rpc):
        print ("sendig Wamp RPC ",rpc)
        self.q_rpc.put(rpc)
        print 'POSTCALL',self.q_rpc.qsize()

        x=''
        #while True:
        if self.b_a_int.poll():
            x= self.b_a_int.recv()
            #break
        return x

